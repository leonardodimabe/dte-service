import { useState, type FormEvent } from "react";
import { api } from "../api";
import { useApi } from "../hooks/useApi";
import type { User } from "../types";

const EMPTY = { email: "", password: "", role: "operator", customer_id: "" };

export default function Users() {
  const { data: items, loading, error, reload } = useApi(() => api.users(), []);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState("");

  async function create(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    try {
      await api.createUser({
        email: form.email,
        password: form.password,
        role: form.role,
        customer_id: form.role === "client" ? Number(form.customer_id) : null,
      });
      setForm(EMPTY);
      await reload();
    } catch (err) {
      setFormError((err as Error).message);
    }
  }

  async function toggle(u: User) {
    setFormError("");
    try {
      await api.setUserActive(u.id, !u.is_active);
      await reload();
    } catch (err) {
      setFormError((err as Error).message);
    }
  }

  return (
    <>
      <h1>Usuarios</h1>
      {error && <p className="error">{error}</p>}
      <div className="card">
        {loading ? (
          <p className="muted">Cargando…</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Rol</th>
                <th>Cliente</th>
                <th>Activo</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {(items ?? []).map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>{u.email}</td>
                  <td>{u.role}</td>
                  <td>{u.customer_id ?? "—"}</td>
                  <td>{u.is_active ? "sí" : "no"}</td>
                  <td>
                    <button className="secondary" onClick={() => toggle(u)}>
                      {u.is_active ? "Desactivar" : "Activar"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <form className="card" onSubmit={create}>
        <h2>Nuevo usuario</h2>
        {formError && <p className="error">{formError}</p>}
        <div className="row">
          <div className="field">
            <label>Email</label>
            <input
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Contraseña</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
            />
          </div>
          <div className="field">
            <label>Rol</label>
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
              <option value="superadmin">superadmin</option>
              <option value="operator">operator</option>
              <option value="auditor">auditor</option>
              <option value="client">client</option>
            </select>
          </div>
          {form.role === "client" && (
            <div className="field">
              <label>customer_id</label>
              <input
                value={form.customer_id}
                onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
                required
              />
            </div>
          )}
          <button>Crear</button>
        </div>
      </form>
    </>
  );
}
