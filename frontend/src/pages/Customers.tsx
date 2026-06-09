import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { canWrite, useAuth } from "../auth";
import { useApi } from "../hooks/useApi";

const EMPTY = {
  name: "",
  key: "",
  rut: "",
  environment: "CERTIFICATION",
  resolution_number: "",
  resolution_date: "",
};

export default function Customers() {
  const { user } = useAuth();
  const { data: items, loading, error, reload } = useApi(() => api.customers(), []);
  const [form, setForm] = useState(EMPTY);
  const [formError, setFormError] = useState("");

  async function create(e: FormEvent) {
    e.preventDefault();
    setFormError("");
    try {
      const payload: {
        name: string;
        key: string;
        rut: string;
        environment: string;
        resolution_number?: number;
        resolution_date?: string;
      } = { name: form.name, key: form.key, rut: form.rut, environment: form.environment };
      if (form.environment === "PRODUCTION") {
        payload.resolution_number = Number(form.resolution_number || 0);
        payload.resolution_date = form.resolution_date;
      }
      await api.createCustomer(payload);
      setForm(EMPTY);
      await reload();
    } catch (err) {
      setFormError((err as Error).message);
    }
  }

  return (
    <>
      <h1>Clientes</h1>
      {error && <p className="error">{error}</p>}
      <div className="card">
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
                  <td>{c.key}</td>
                  <td>{c.rut}</td>
                  <td>{c.environment}</td>
                  <td>
                    <Link to={`/customers/${c.id}`}>Gestionar →</Link>
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

      {canWrite(user?.role) && (
        <form className="card" onSubmit={create}>
          <h2>Nuevo cliente</h2>
          {formError && <p className="error">{formError}</p>}
          <div className="row">
            <div className="field">
              <label>Nombre</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="field">
              <label>Código (customerCode)</label>
              <input
                value={form.key}
                onChange={(e) => setForm({ ...form, key: e.target.value })}
                required
              />
            </div>
            <div className="field">
              <label>RUT</label>
              <input
                value={form.rut}
                onChange={(e) => setForm({ ...form, rut: e.target.value })}
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
            <button>Crear</button>
          </div>
        </form>
      )}
    </>
  );
}
