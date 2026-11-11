"""
Dual-path AI layer: a single OpenAI chat-completion call when
`OPENAI_API_KEY` is set, otherwise a fully offline, deterministic stub. This
lets the entire insights pipeline (aggregation, seed data, the generate
endpoint, tests) be built, run, and tested with zero network access and
zero cost.

Unlike ticket-triage's `apps/common/ai.py` (which this module takes its
docstring style and dual-path shape from), there is no embeddings step and
no vector search here - this app is plain Postgres, no pgvector. The AI's
only job is to turn numbers Django/Postgres already computed
(`apps/insights/services.py`) into a narrative paragraph. The AI never
sees individual raw transactions, only the aggregates passed in below.

*** NOTE ON MODEL NAME ***: this app defaults `OPENAI_CHAT_MODEL` to
`"gpt-5.4-mini"` (overridable via the `OPENAI_CHAT_MODEL` env var). This is
deliberately different from the `"gpt-5.6-sol"` default used by several
sibling apps in this workspace.

Stub path (default - `OPENAI_API_KEY` unset, used for local dev/tests): the
narrative is synthesized directly from the structured numbers with
straightforward string templating - arguably more "real" here than a
random stub would be, since the inputs are already numeric. Categories are
sorted by total descending (ties broken by name) before any sentence is
built, so the same `(month, category_totals, total_income,
total_expenses, prior_month_category_totals)` inputs always produce the
exact same narrative string, byte-for-byte, regardless of the input
dicts' key order.
"""
from django.conf import settings


def is_stub_mode() -> bool:
    return not bool(settings.OPENAI_API_KEY)


def generate_budget_insights(
    month: str,
    category_totals: dict,
    total_income: float,
    total_expenses: float,
    prior_month_category_totals: dict | None,
) -> str:
    """Return a natural-language narrative (one to a few short paragraphs)
    explaining spending patterns for `month`.

    Real path (`OPENAI_API_KEY` set): calls the OpenAI chat completions API
    with `settings.OPENAI_CHAT_MODEL`.
    Stub path (no key): deterministic templated string - see module
    docstring.
    """
    if settings.OPENAI_API_KEY:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        prompt = _build_prompt(
            month, category_totals, total_income, total_expenses, prior_month_category_totals
        )
        response = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a personal budgeting assistant. Narrate the "
                        "given month's spending aggregates in one to three "
                        "short, concrete paragraphs (e.g. largest categories, "
                        "notable month-over-month changes, income vs "
                        "expenses). Use only the figures given - never invent "
                        "transactions or categories that are not listed."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    return _stub_narrative(
        month, category_totals, total_income, total_expenses, prior_month_category_totals
    )


def _build_prompt(
    month: str,
    category_totals: dict,
    total_income: float,
    total_expenses: float,
    prior_month_category_totals: dict | None,
) -> str:
    lines = [
        f"Month: {month}",
        f"Total income: ${total_income:,.2f}",
        f"Total expenses: ${total_expenses:,.2f}",
        "Category totals (expenses):",
    ]
    for name, total in _sorted_categories(category_totals):
        lines.append(f"  - {name}: ${total:,.2f}")
    if prior_month_category_totals:
        lines.append("Prior month category totals (expenses):")
        for name, total in _sorted_categories(prior_month_category_totals):
            lines.append(f"  - {name}: ${total:,.2f}")
    return "\n".join(lines)


def _sorted_categories(category_totals: dict) -> list:
    """Sort (name, total) pairs by total descending, ties broken by name
    ascending, so output never depends on the caller's dict ordering."""
    return sorted(category_totals.items(), key=lambda item: (-item[1], item[0]))


def _pct_change(current: float, prior) -> float | None:
    if prior is None or prior == 0:
        return None
    return ((current - prior) / prior) * 100.0


def _stub_narrative(
    month: str,
    category_totals: dict,
    total_income: float,
    total_expenses: float,
    prior_month_category_totals: dict | None,
) -> str:
    prior = prior_month_category_totals or {}
    sorted_categories = _sorted_categories(category_totals)

    if not sorted_categories:
        spending_sentence = f"You recorded no expenses in {month}."
    else:
        top = sorted_categories[:3]
        parts = []
        for name, total in top:
            change = _pct_change(total, prior.get(name))
            if change is None:
                parts.append(f"${total:,.2f} on {name}")
            elif change >= 0:
                parts.append(f"${total:,.2f} on {name} ({change:.0f}% more than last month)")
            else:
                parts.append(f"${total:,.2f} on {name} ({abs(change):.0f}% less than last month)")

        if len(parts) == 1:
            joined = parts[0]
        elif len(parts) == 2:
            joined = f"{parts[0]} and {parts[1]}"
        else:
            joined = f"{', '.join(parts[:-1])}, and {parts[-1]}"

        top_name, top_total = sorted_categories[0]
        spending_sentence = (
            f"In {month}, you spent {joined}. "
            f"Your largest expense category was {top_name} at ${top_total:,.2f}."
        )

    net = total_income - total_expenses
    if net >= 0:
        summary_sentence = (
            f"Total income was ${total_income:,.2f} against ${total_expenses:,.2f} in "
            f"expenses, leaving a surplus of ${net:,.2f}."
        )
    else:
        summary_sentence = (
            f"Total income was ${total_income:,.2f} against ${total_expenses:,.2f} in "
            f"expenses, a shortfall of ${abs(net):,.2f}."
        )

    return f"{spending_sentence} {summary_sentence}"
