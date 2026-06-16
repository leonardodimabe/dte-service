import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { canWrite, useAuth } from "../auth";
import Modal from "../components/Modal";
import { useApi } from "../hooks/useApi";
import type { Customer } from "../types";

const EMPTY = {
  name: "",
  rut: "",
  environment: "CERTIFICATION",
  resolution_number: "",
  resolution_date: "",
};

export default function Customers() {
  const { user } = useAuth();
  const writable = canWrite(user?.role);
  const { data: items, loading, error, reload } = useApi(() => api.customers(), []);

  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState("");
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<Customer | null>(null);

  function openCreate() {
    setEditing(null);
    setForm(EMPTY);
    setFormError("");
    setCreated(null);
    setOpen(true);
  }

  function openEdit(c: Customer) {
    setEditing(c);
    setForm({ ...EMPTY, name: c.name, rut: c.rut, environment: c.environment });
    setFormError("");
    setCreated(null);
    setOpen(true);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    setBusy(true);
    try {
      const payload: {
        name: string;
        rut: string;
        environment: string;
        resolution_number?: number;
        resolution_date?: string;
      } = { name: form.name, rut: form.rut, environment: form.environment };
      if (form.environment === "PRODUCTION" && form.resolution_number) {
        payload.resolution_number = Number(form.resolution_number);
        if (form.resolution_date) payload.resolution_date = form.resolution_date;
      }
      if (editing) {
        await api.updateCustomer(editing.id, payload);
      } else {
        // No se envía `key`: el servidor genera el customerCode automáticamente.
        setCreated(await api.createCustomer(payload));
      }
      setOpen(false);
      await reload();
    } catch (err) {
      setFormError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {error && <p className="error">{error}</p>}

      {created && (
        <div className="notice ok">
          Cliente <strong>{created.name}</strong> creado. Su código de cliente generado es:
          <div className="secret">
            <span className="code">{created.key}</span>
            <button
              className="secondary sm"
              type="button"
              onClick={() => navigator.clipboard?.writeText(created.key)}
            >
              Copiar
            </button>
            <Link to={`/customers/${created.id}`}>Gestionar →</Link>
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-head">
          <h2>Clientes registrados</h2>
          <span className="spacer" />
          {writable && (
            <button className="add" onClick={openCreate}>
              Nuevo cliente
            </button>
          )}
        </div>
        {loading ? (
          <p className="muted">Cargando…</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Nombre</th>
                <th>Código</th>
                <th>RUT</th>
                <th>Ambiente</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {(items ?? []).map((c) => (
                <tr key={c.id}>
                  <td>{c.id}</td>
                  <td>{c.name}</td>
                  <td>
                    <span className="code">{c.key}</span>
                  </td>
                  <td>{c.rut}</td>
                  <td>
                    <span className={`badge ${c.environment === "PRODUCTION" ? "denied" : "ok"}`}>
                      {c.environment}
                    </span>
                  </td>
                  <td>
                    <div className="actions">
                      <Link to={`/customers/${c.id}`}>Gestionar →</Link>
                      {writable && (
                        <button className="btn-link" type="button" onClick={() => openEdit(c)}>
                          Editar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {items && items.length === 0 && (
                <tr>
                  <td colSpan={6} className="muted">
                    Sin clientes.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {open && (
        <Modal
          title={editing ? `Editar cliente · ${editing.name}` : "Nuevo cliente"}
          onClose={() => setOpen(false)}
          footer={
            <>
              <button className="secondary" type="button" onClick={() => setOpen(false)}>
                Cancelar
              </button>
              <button type="submit" form="customer-form" disabled={busy}>
                {editing ? "Guardar cambios" : "Crear cliente"}
              </button>
            </>
          }
        >
          <form id="customer-form" className="form-grid" onSubmit={submit}>
            {formError && <p className="error">{formError}</p>}
            {editing ? (
              <div className="field">
                <label>Código de cliente (no editable)</label>
                <span className="code">{editing.key}</span>
              </div>
            ) : (
              <p className="muted" style={{ margin: 0 }}>
                El código de cliente (customerCode) se genera automáticamente.
              </p>
            )}
            <div className="field">
              <label>Nombre</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="field">
              <label>RUT</label>
              <input
                value={form.rut}
                onChange={(e) => setForm({ ...form, rut: e.target.value })}
                placeholder="76158145-7"
                required
              />
            </div>
            <div className="field">
              <label>Ambiente</label>
              <select
                value={form.environment}
                onChange={(e) => setForm({ ...form, environment: e.target.value })}
              >
                <option value="CERTIFICATION">Certificación</option>
                <option value="PRODUCTION">Producción</option>
              </select>
            </div>
            {form.environment === "PRODUCTION" && (
              <>
                <div className="field">
                  <label>N° resolución</label>
                  <input
                    value={form.resolution_number}
                    onChange={(e) => setForm({ ...form, resolution_number: e.target.value })}
                    placeholder={editing ? "(dejar vacío = sin cambio)" : ""}
                  />
                </div>
                <div className="field">
                  <label>Fecha resolución</label>
                  <input
                    type="date"
                    value={form.resolution_date}
                    onChange={(e) => setForm({ ...form, resolution_date: e.target.value })}
                  />
                </div>
              </>
            )}
          </form>
        </Modal>
      )}
    </>
  );
}
