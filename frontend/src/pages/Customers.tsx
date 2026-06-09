import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { canWrite, useAuth } from "../auth";
import type { Customer } from "../types";

const EMPTY = { name: "", key: "", rut: "", environment: "CERTIFICATION" };

export default function Customers() {
  const { user } = useAuth();
  const [items, setItems] = useState<Customer[]>([]);
  const [error, setError] = useState("");
  const [form, setForm] = useState(EMPTY);

  function reload() {
    api
      .customers()
      .then(setItems)
      .catch((e) => setError((e as Error).message));
  }
  useEffect(() => {
    reload();
  }, []);

  async function create(e: FormEvent) {
    e.preventDefault();
    setError("");
    try {
      await api.createCustomer(form);
      setForm(EMPTY);
      reload();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      <h1>Clientes</h1>
      {error && <p className="error">{error}</p>}
      <div className="card">
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
            {items.map((c) => (
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
            {items.length === 0 && (
              <tr>
                <td colSpan={6} className="muted">
                  Sin clientes.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {canWrite(user?.role) && (
        <form className="card" onSubmit={create}>
          <h2>Nuevo cliente</h2>
          <div className="row">
            <div className="field">
              <label>Nombre</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="field">
              <label>Código (customerCode)</label>
              <input value={form.key} onChange={(e) => setForm({ ...form, key: e.target.value })} required />
            </div>
            <div className="field">
              <label>RUT</label>
              <input value={form.rut} onChange={(e) => setForm({ ...form, rut: e.target.value })} required />
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
            <button>Crear</button>
          </div>
        </form>
      )}
    </>
  );
}
