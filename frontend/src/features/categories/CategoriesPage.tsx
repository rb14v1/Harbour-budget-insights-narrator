import { useEffect, useState, type FormEvent } from "react";

import { createCategory, deleteCategory, listCategories, updateCategory } from "../../api/categories";
import { extractErrorMessage } from "../../api/client";
import type { Category } from "../../types";

export function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [editing, setEditing] = useState<Category | null>(null);
  const [name, setName] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await listCategories();
      setCategories(res.data.results);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function resetForm() {
    setEditing(null);
    setName("");
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      if (editing) {
        await updateCategory(editing.id, name);
      } else {
        await createCategory(name);
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
    if (!confirm("Delete this category? This fails if it still has transactions.")) return;
    setError(null);
    try {
      await deleteCategory(id);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err));
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Categories</h1>
      </div>

      <div className="card">
        <form className="inline-form" onSubmit={handleSubmit}>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <button type="submit" disabled={submitting}>{editing ? "Save" : "Add category"}</button>
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
                <th>Name</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {categories.map((c) => (
                <tr key={c.id}>
                  <td>{c.name}</td>
                  <td className="actions">
                    <button className="secondary" onClick={() => { setEditing(c); setName(c.name); }}>Edit</button>
                    <button className="danger" onClick={() => handleDelete(c.id)}>Delete</button>
                  </td>
                </tr>
              ))}
              {categories.length === 0 && (
                <tr><td colSpan={2} className="muted">No categories yet.</td></tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
