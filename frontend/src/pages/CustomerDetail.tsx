import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { canWrite, useAuth } from "../auth";
import type { Customer, RcvResponse, ServiceInfo } from "../types";

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(((reader.result as string).split(",")[1] ?? ""));
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

  const [customer, setCustomer] = useState<Customer | null>(null);
  const [services, setServices] = useState<ServiceInfo[]>([]);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const [grantSvc, setGrantSvc] = useState("");
  const [grantKey, setGrantKey] = useState("");
  const [certFile, setCertFile] = useState<File | null>(null);
  const [certPass, setCertPass] = useState("");
  const [cafFile, setCafFile] = useState<File | null>(null);
  const [period, setPeriod] = useState("");
  const [operation, setOperation] = useState("COMPRA");
  const [rcv, setRcv] = useState<RcvResponse | null>(null);

  useEffect(() => {
    api
      .customers()
      .then((list) => setCustomer(list.find((c) => c.id === cid) ?? null))
      .catch((e) => setError((e as Error).message));
    api.services().then(setServices).catch(() => undefined);
  }, [cid]);

  function run(action: () => Promise<unknown>, ok: string) {
    setError("");
    setMsg("");
    action()
      .then(() => setMsg(ok))
      .catch((e) => setError((e as Error).message));
  }

  function grant(e: FormEvent) {
    e.preventDefault();
    run(() => api.grant(cid, grantSvc, grantKey), `Servicio habilitado. apiKey: ${grantKey}`);
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
    setError("");
    api
      .rcv(cid, period, operation)
      .then(setRcv)
      .catch((err) => setError((err as Error).message));
  }

  if (!customer) return <p className="muted">Cargando cliente…</p>;

  return (
    <>
      <p>
        <Link to="/customers">← Clientes</Link>
      </p>
      <h1>{customer.name}</h1>
      <p className="muted">
        Código {customer.key} · RUT {customer.rut} · {customer.environment}
      </p>
      {msg && <p style={{ color: "var(--ok)" }}>{msg}</p>}
      {error && <p className="error">{error}</p>}

      {writable && (
        <>
          <form className="card" onSubmit={grant}>
            <h2>Habilitar servicio</h2>
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
                <label>apiKey (se guarda hasheada)</label>
                <input value={grantKey} onChange={(e) => setGrantKey(e.target.value)} required />
              </div>
              <button>Habilitar</button>
            </div>
          </form>

          <form className="card" onSubmit={uploadCert}>
            <h2>Certificado (.pfx)</h2>
            <div className="row">
              <input type="file" accept=".pfx,.p12" onChange={(e) => setCertFile(e.target.files?.[0] ?? null)} />
              <input type="password" placeholder="contraseña" value={certPass} onChange={(e) => setCertPass(e.target.value)} />
              <button disabled={!certFile}>Subir</button>
            </div>
          </form>

          <form className="card" onSubmit={uploadCaf}>
            <h2>CAF (folios)</h2>
            <div className="row">
              <input type="file" accept=".xml" onChange={(e) => setCafFile(e.target.files?.[0] ?? null)} />
              <button disabled={!cafFile}>Subir</button>
            </div>
          </form>
        </>
      )}

      <form className="card" onSubmit={queryRcv}>
        <h2>RCV (operador)</h2>
        <div className="row">
          <div className="field">
            <label>Período (AAAAMM)</label>
            <input value={period} onChange={(e) => setPeriod(e.target.value)} placeholder="202505" required />
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
  );
}
