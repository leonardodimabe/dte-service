import { useState, type FormEvent } from "react";
import { api } from "../api";
import Modal from "../components/Modal";
import { useApi } from "../hooks/useApi";
import type { User } from "../types";

const EMPTY = { email: "", password: "", role: "operator", customer_id: "" };

export default function Users() {
  const { data: items, loading, error, reload } = useApi(() => api.users(), []);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");

  function openCreate() {
    setForm(EMPTY);
    setFormError("");
    setOpen(true);
  }

  async function create(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    setBusy(true);
    try {
      await api.createUser({
        email: form.email,
        password: form.password,
        role: form.role,
        customer_id: form.role === "client" ? Number(form.customer_id) : null,
      });
      setOpen(false);
      await reload();
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function toggle(u: User) {
    setActionError("");
    try {
      await api.setUserActive(u.id, !u.is_active);
      await reload();
    } catch (err) {
      setActionError((err as Error).message);
    }
  }

  return (
    <>
      {error && <p className="error">{error}</p>}
      {actionError && <p className="error">{actionError}</p>}

      <div className="card">
        <div className="card-head">
          <h2>Usuarios del portal</h2>
          <span className="spacer" />
          <button className="add" onClick={openCreate}>
            Nuevo usuario
          </button>
        </div>
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
                  <td>
                    <span className={`badge ${u.is_active ? "ok" : "error"}`}>
                      {u.is_active ? "sí" : "no"}
                    </span>
                  </td>
                  <td>
                    <button className="secondary sm" onClick={() => toggle(u)}>
                      {u.is_active ? "Desactivar" : "Activar"}
                    </button>
                  </td>
                </tr>
              ))}
              {items && items.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">
                    Sin usuarios.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {open && (
        <Modal
          title="Nuevo usuario"
          onClose={() => setOpen(false)}
          footer={
            <>
              <button className="secondary" type="button" onClick={() => setOpen(false)}>
                Cancelar
              </button>
              <button type="submit" form="user-form" disabled={busy}>
                Crear usuario
              </button>
            </>
          }
        >
          <form id="user-form" className="form-grid" onSubmit={create}>
            {formError && <p className="error">{formError}</p>}
            <div className="field">
              <label>Email</label>
              <input
                type="email"
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
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
              >
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
          </form>
        </Modal>
      )}
    </>
  );
}
