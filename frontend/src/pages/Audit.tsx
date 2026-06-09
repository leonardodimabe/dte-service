import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import type { AdminAudit, RequestLog } from "../types";

export default function Audit() {
  const { user } = useAuth();
  const isClient = user?.role === "client";
  const [tab, setTab] = useState<"requests" | "changes">("requests");
  const [requests, setRequests] = useState<RequestLog[]>([]);
  const [changes, setChanges] = useState<AdminAudit[]>([]);
  const [service, setService] = useState("");
  const [outcome, setOutcome] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadRequests() {
    setLoading(true);
    setError("");
    try {
      const params: Record<string, string> = { limit: "200" };
      if (service) params.service_code = service;
      if (outcome) params.outcome = outcome;
      setRequests(await api.auditRequests(params));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function loadChanges() {
    setLoading(true);
    setError("");
    try {
      setChanges(await api.auditChanges());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (tab === "requests") void loadRequests();
    else void loadChanges();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  async function exportCsv() {
    setError("");
    try {
      await api.downloadAuditCsv();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <>
      <h1>Auditoría</h1>
      {error && <p className="error">{error}</p>}
      <div className="tabs">
        <button className={tab === "requests" ? "active" : ""} onClick={() => setTab("requests")}>
          Peticiones
        </button>
        {!isClient && (
          <button className={tab === "changes" ? "active" : ""} onClick={() => setTab("changes")}>
            Cambios
          </button>
        )}
      </div>

      {tab === "requests" && (
        <div className="card">
          <div className="row" style={{ marginBottom: "1rem" }}>
            <div className="field">
              <label>service_code</label>
              <input value={service} onChange={(e) => setService(e.target.value)} />
            </div>
            <div className="field">
              <label>resultado</label>
              <select value={outcome} onChange={(e) => setOutcome(e.target.value)}>
                <option value="">todos</option>
                <option value="ok">ok</option>
                <option value="denied">denied</option>
                <option value="error">error</option>
              </select>
            </div>
            <button onClick={loadRequests} disabled={loading}>
              Filtrar
            </button>
            <button className="secondary" onClick={exportCsv}>
              Exportar CSV
            </button>
          </div>
          {loading ? (
            <p className="muted">Cargando…</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Principal</th>
                  <th>Servicio</th>
                  <th>Método</th>
                  <th>Ruta</th>
                  <th>Estado</th>
                  <th>ms</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((r) => (
                  <tr key={r.id}>
                    <td>{r.created_at.replace("T", " ").slice(0, 19)}</td>
                    <td>
                      {r.principal_type}
                      {r.principal_id ? `#${r.principal_id}` : ""}
                    </td>
                    <td>{r.service_code ?? "—"}</td>
                    <td>{r.method}</td>
                    <td>{r.path}</td>
                    <td>
                      <span className={`badge ${r.outcome}`}>{r.status_code}</span>
                    </td>
                    <td>{r.latency_ms}</td>
                  </tr>
                ))}
                {requests.length === 0 && (
                  <tr>
                    <td colSpan={7} className="muted">
                      Sin registros.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      )}

      {tab === "changes" && !isClient && (
        <div className="card">
          {loading ? (
            <p className="muted">Cargando…</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Fecha</th>
                  <th>Actor</th>
                  <th>Acción</th>
                  <th>Objetivo</th>
                  <th>Detalle</th>
                </tr>
              </thead>
              <tbody>
                {changes.map((c) => (
                  <tr key={c.id}>
                    <td>{c.created_at.replace("T", " ").slice(0, 19)}</td>
                    <td>{c.actor_user_id ?? "máquina"}</td>
                    <td>{c.action}</td>
                    <td>
                      {c.target_type}#{c.target_id}
                    </td>
                    <td>{c.summary}</td>
                  </tr>
                ))}
                {changes.length === 0 && (
                  <tr>
                    <td colSpan={5} className="muted">
                      Sin cambios.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      )}
    </>
  );
}
