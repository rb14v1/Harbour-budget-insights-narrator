import { useEffect, useState } from "react";

import { extractErrorMessage } from "../../api/client";
import { fetchInsight, generateInsight } from "../../api/insights";
import type { MonthlyInsightResponse } from "../../types";
import { currentYearMonth, formatDateTime, formatMoney } from "../../utils/format";

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export function InsightsPage() {
  const initial = currentYearMonth();
  const [year, setYear] = useState(initial.year);
  const [month, setMonth] = useState(initial.month);
  const [data, setData] = useState<MonthlyInsightResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchInsight(year, month);
      setData(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [year, month]);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const res = await generateInsight(year, month);
      setData(res.data);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setGenerating(false);
    }
  }

  const categoryEntries = data
    ? Object.entries(data.category_totals).sort((a, b) => b[1] - a[1])
    : [];
  const net = data ? data.total_income - data.total_expenses : 0;

  return (
    <div>
      <div className="page-header">
        <h1>Insights</h1>
        <div className="month-picker">
          <select value={month} onChange={(e) => setMonth(Number(e.target.value))}>
            {MONTH_NAMES.map((name, idx) => (
              <option key={name} value={idx + 1}>{name}</option>
            ))}
          </select>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            style={{ width: "5.5rem" }}
          />
        </div>
      </div>

      {error && <div className="form-error">{error}</div>}

      {loading || !data ? (
        <p>Loading...</p>
      ) : (
        <>
          <div className="summary-grid">
            <div className="summary-tile">
              <div className="label">Total income</div>
              <div className="value positive">{formatMoney(data.total_income)}</div>
            </div>
            <div className="summary-tile">
              <div className="label">Total expenses</div>
              <div className="value">{formatMoney(data.total_expenses)}</div>
            </div>
            <div className="summary-tile">
              <div className="label">Net</div>
              <div className={`value ${net >= 0 ? "positive" : "negative"}`}>{formatMoney(net)}</div>
            </div>
          </div>

          <div className="card">
            <h2>Spending by category</h2>
            {categoryEntries.length === 0 && <p className="muted">No expenses recorded for this month.</p>}
            {categoryEntries.map(([name, total]) => {
              const pct = data.total_expenses > 0 ? (total / data.total_expenses) * 100 : 0;
              return (
                <div className="category-row" key={name}>
                  <div className="category-row-header">
                    <span>{name}</span>
                    <span>{formatMoney(total)}</span>
                  </div>
                  <div className="progress-bar-track">
                    <div className="progress-bar-fill" style={{ width: `${Math.min(100, pct)}%` }} />
                  </div>
                </div>
              );
            })}
          </div>

          <div className="card">
            <div className="page-header">
              <h2>AI narrative</h2>
              <button onClick={handleGenerate} disabled={generating}>
                {generating ? "Generating..." : data.narrative ? "Regenerate" : "Generate insights"}
              </button>
            </div>
            {data.narrative ? (
              <>
                <p className="narrative-block">{data.narrative}</p>
                <p className="muted">Generated {formatDateTime(data.generated_at)}</p>
              </>
            ) : (
              <p className="muted">No narrative generated yet for this month.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
