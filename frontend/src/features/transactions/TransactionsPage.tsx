import { useEffect, useState, type FormEvent } from "react";

import { listCategories } from "../../api/categories";
import { extractErrorMessage } from "../../api/client";
import { createTransaction, deleteTransaction, listTransactions, updateTransaction } from "../../api/transactions";
import type { Category, Transaction, TransactionType } from "../../types";
import { formatMoney, today } from "../../utils/format";

export function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [monthFilter, setMonthFilter] = useState(today().slice(0, 7));
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState<Transaction | null>(null);
  const [categoryId, setCategoryId] = useState<string>("");
  const [transactionType, setTransactionType] = useState<TransactionType>("expense");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [transactionDate, setTransactionDate] = useState(today());
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [txRes, catRes] = await Promise.all([
        listTransactions(monthFilter || undefined),
        listCategories(),
      ]);
      setTransactions(txRes.data.results);
      setCategories(catRes.data.results);
      if (!categoryId && catRes.data.results.length > 0) {
        setCategoryId(String(catRes.data.results[0].id));
      }
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [monthFilter]);

  function resetForm() {
    setEditing(null);
    setTransactionType("expense");
    setAmount("");
    setDescription("");
    setTransactionDate(today());
  }

  function startEdit(txn: Transaction) {
    setEditing(txn);
    setCategoryId(String(txn.category));
    setTransactionType(txn.transaction_type);
    setAmount(txn.amount);
    setDescription(txn.description);
    setTransactionDate(txn.transaction_date);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const payload = {
        category: Number(categoryId),
        transaction_type: transactionType,
        amount,
        description,
        transaction_date: transactionDate,
      };
      if (editing) {
        await updateTransaction(editing.id, payload);
      } else {
        await createTransaction(payload);
      }
      resetForm();
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("Delete this transaction?")) return;
    setError(null);
    try {
      await deleteTransaction(id);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Transactions</h1>
        <label className="checkbox-label">
          Month
          <input type="month" value={monthFilter} onChange={(e) => setMonthFilter(e.target.value)} />
        </label>
      </div>

      <div className="card">
        <form className="inline-form" onSubmit={handleSubmit}>
          <label>
            Category
            <select value={categoryId} onChange={(e) => setCategoryId(e.target.value)} required>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </label>
          <label>
            Type
            <select value={transactionType} onChange={(e) => setTransactionType(e.target.value as TransactionType)}>
              <option value="expense">Expense</option>
              <option value="income">Income</option>
            </select>
          </label>
          <label>
            Amount
            <input type="number" step="0.01" min="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} required />
          </label>
          <label>
            Date
            <input type="date" value={transactionDate} onChange={(e) => setTransactionDate(e.target.value)} required />
          </label>
          <label>
            Description
            <input value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
          <button type="submit" disabled={submitting}>{editing ? "Save" : "Add transaction"}</button>
          {editing && <button type="button" className="secondary" onClick={resetForm}>Cancel</button>}
        </form>
        {error && <div className="form-error">{error}</div>}
      </div>

      <div className="card">
        {loading ? (
          <p>Loading...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Description</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((t) => (
                <tr key={t.id}>
                  <td>{t.transaction_date}</td>
                  <td>{t.category_name}</td>
                  <td>{t.transaction_type}</td>
                  <td>{formatMoney(t.amount)}</td>
                  <td>{t.description || <span className="muted">-</span>}</td>
                  <td className="actions">
                    <button className="secondary" onClick={() => startEdit(t)}>Edit</button>
                    <button className="danger" onClick={() => handleDelete(t.id)}>Delete</button>
                  </td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr><td colSpan={6} className="muted">No transactions for this month.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
