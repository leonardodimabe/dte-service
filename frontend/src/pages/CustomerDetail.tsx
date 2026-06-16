import { useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { canWrite, useAuth } from "../auth";
import { useApi } from "../hooks/useApi";
import type { RcvResponse } from "../types";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string).split(",")[1] ?? "");
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

const money = (n: number) => "$" + n.toLocaleString("es-CL");

export default function CustomerDetail() {
  const { id } = useParams();
  const cid = Number(id);
  const { user } = useAuth();
  const writable = canWrite(user?.role);

  const { data, loading, error, reload } = useApi(async () => {
    const [customer, granted, certs, cafs, services] = await Promise.all([
      api.customer(cid),
      api.customerServices(cid),
      api.customerCerts(cid),
      api.customerCafs(cid),
      api.services(),
    ]);
    return { customer, granted, certs, cafs, services };
  }, [cid]);

  const [msg, setMsg] = useState("");
  const [actionError, setActionError] = useState("");
  const [grantSvc, setGrantSvc] = useState("");
  const [grantKey, setGrantKey] = useState("");
  const [grantedKey, setGrantedKey] = useState<string | null>(null);
  const [certFile, setCertFile] = useState<File | null>(null);
  const [certPass, setCertPass] = useState("");
  const [cafFile, setCafFile] = useState<File | null>(null);
  const [period, setPeriod] = useState("");
  const [operation, setOperation] = useState("COMPRA");
  const [rcv, setRcv] = useState<RcvResponse | null>(null);

  function run(action: () => Promise<unknown>, ok: string) {
    setActionError("");
    setMsg("");
    action()
      .then(() => {
        setMsg(ok);
        return reload();
      })
      .catch((e) => setActionError((e as Error).message));
  }

  function grant(e: FormEvent) {
    e.preventDefault();
    setActionError("");
    setMsg("");
    setGrantedKey(null);
    api
      .grant(cid, grantSvc, grantKey || undefined)
      .then((res) => {
        setMsg("Servicio habilitado.");
        setGrantedKey(res.apikey ?? (grantKey || null));
        setGrantSvc("");
        setGrantKey("");
        return reload();
      })
      .catch((err) => setActionError((err as Error).message));
  }
  function revoke(code: string) {
    run(() => api.revokeService(cid, code), "Servicio revocado.");
  }
  async function uploadCert(e: FormEvent) {
    e.preventDefault();
    if (!certFile) return;
    const b64 = await fileToBase64(certFile);
    run(() => api.uploadCert(cid, b64, certPass), "Certificado cargado.");
  }
  async function uploadCaf(e: FormEvent) {
    e.preventDefault();
    if (!cafFile) return;
    const b64 = await fileToBase64(cafFile);
    run(() => api.uploadCaf(cid, b64), "CAF cargado.");
  }
  function queryRcv(e: FormEvent) {
    e.preventDefault();
    setActionError("");
    api
      .rcv(cid, period, operation)
      .then(setRcv)
      .catch((err) => setActionError((err as Error).message));
  }

  if (!data) {
    if (loading) return <p className="muted">Cargando cliente…</p>;
    if (error) return <p className="error">{error}</p>;
    return null;
  }
  const { customer, granted, certs, cafs, services } = data;

  return (
    <>
      <p>
        <Link to="/customers">← Clientes</Link>
      </p>
      <h1>{customer.name}</h1>
      <p className="muted">
        Código {customer.key} · RUT {customer.rut} · {customer.environment}
      </p>
      {msg && !grantedKey && <p style={{ color: "var(--ok)" }}>{msg}</p>}
      {actionError && <p className="error">{actionError}</p>}
      {grantedKey && (
        <div className="notice ok">
          {msg} Copia la <strong>apiKey</strong> ahora — no se vuelve a mostrar:
          <div className="secret">
            <span className="code">{grantedKey}</span>
            <button
              className="secondary sm"
              type="button"
              onClick={() => navigator.clipboard?.writeText(grantedKey)}
            >
              Copiar
            </button>
          </div>
        </div>
      )}

      <div className="card">
        <h2>Servicios habilitados</h2>
        <table>
          <thead>
            <tr>
              <th>Servicio</th>
              <th>Código</th>
              {writable && <th />}
            </tr>
          </thead>
          <tbody>
            {granted.map((s) => (
              <tr key={s.service_code}>
                <td>{s.name}</td>
                <td className="muted">{s.service_code}</td>
                {writable && (
                  <td>
                    <button className="secondary" onClick={() => revoke(s.service_code)}>
                      Revocar
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {granted.length === 0 && (
              <tr>
                <td colSpan={writable ? 3 : 2} className="muted">
                  Sin servicios habilitados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Certificados</h2>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Vence</th>
              <th>Cargado</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {certs.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.due_date}</td>
                <td>{c.created_at.slice(0, 10)}</td>
                <td>
                  <span className={`badge ${c.expired ? "error" : "ok"}`}>
                    {c.expired ? "vencido" : "vigente"}
                  </span>
                </td>
              </tr>
            ))}
            {certs.length === 0 && (
              <tr>
                <td colSpan={4} className="muted">
                  Sin certificados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>CAF / folios</h2>
        <table>
          <thead>
            <tr>
              <th>Tipo</th>
              <th>Desde</th>
              <th>Hasta</th>
              <th>Último usado</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {cafs.map((c) => (
              <tr key={c.id}>
                <td>{c.doc_type}</td>
                <td>{c.folio_from}</td>
                <td>{c.folio_to}</td>
                <td>{c.last_folio || "—"}</td>
                <td>
                  <span className={`badge ${c.exhausted ? "denied" : "ok"}`}>
                    {c.exhausted ? "agotado" : "disponible"}
                  </span>
                </td>
              </tr>
            ))}
            {cafs.length === 0 && (
              <tr>
                <td colSpan={5} className="muted">
                  Sin CAF cargados.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {writable && (
        <>
          <form className="card" onSubmit={grant}>
            <h2>Habilitar / rotar servicio</h2>
            <div className="row">
              <div className="field">
                <label>Servicio</label>
                <select value={grantSvc} onChange={(e) => setGrantSvc(e.target.value)} required>
                  <option value="">—</option>
                  {services.map((s) => (
                    <option key={s.code} value={s.code}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>apiKey (opcional — se genera si la dejas vacía)</label>
                <input
                  value={grantKey}
                  onChange={(e) => setGrantKey(e.target.value)}
                  placeholder="(autogenerada)"
                />
              </div>
              <button>Guardar</button>
            </div>
          </form>

          <form className="card" onSubmit={uploadCert}>
            <h2>Subir certificado (.pfx)</h2>
            <div className="row">
              <input
                type="file"
                accept=".pfx,.p12"
                onChange={(e) => setCertFile(e.target.files?.[0] ?? null)}
              />
              <input
                type="password"
                placeholder="contraseña"
                value={certPass}
                onChange={(e) => setCertPass(e.target.value)}
              />
              <button disabled={!certFile}>Subir</button>
            </div>
          </form>

          <form className="card" onSubmit={uploadCaf}>
            <h2>Subir CAF</h2>
            <div className="row">
              <input
                type="file"
                accept=".xml"
                onChange={(e) => setCafFile(e.target.files?.[0] ?? null)}
              />
              <button disabled={!cafFile}>Subir</button>
            </div>
          </form>

          <form className="card" onSubmit={queryRcv}>
            <h2>RCV (operador)</h2>
            <div className="row">
              <div className="field">
                <label>Período (AAAAMM)</label>
                <input
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  placeholder="202505"
                  required
                />
              </div>
              <div className="field">
                <label>Operación</label>
                <select value={operation} onChange={(e) => setOperation(e.target.value)}>
                  <option value="COMPRA">Compras</option>
                  <option value="VENTA">Ventas</option>
                </select>
              </div>
              <button>Consultar</button>
            </div>
            {rcv && (
              <table style={{ marginTop: "1rem" }}>
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Folio</th>
                    <th>RUT</th>
                    <th>Nombre</th>
                    <th>Fecha</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {rcv.documents.map((d, i) => (
                    <tr key={i}>
                      <td>{d.doc_type}</td>
                      <td>{d.folio}</td>
                      <td>{d.counterpart_rut}</td>
                      <td>{d.counterpart_name}</td>
                      <td>{d.date}</td>
                      <td>{money(d.total_amount)}</td>
                    </tr>
                  ))}
                  {rcv.count === 0 && (
                    <tr>
                      <td colSpan={6} className="muted">
                        Sin documentos en el período.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            )}
          </form>
        </>
      )}
    </>
  );
}
