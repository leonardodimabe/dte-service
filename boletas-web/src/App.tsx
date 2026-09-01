import { useEffect, useState } from "react";
import { decodeHtml, fetchIssuer, lookupReceipt, type Receipt } from "./api";

/** Formato chileno: separador de miles con punto. */
const money = (value: number) => "$" + value.toLocaleString("es-CL");

export default function App() {
  const [issuerName, setIssuerName] = useState("");
  const [folio, setFolio] = useState("");
  const [issueDate, setIssueDate] = useState("");
  const [totalAmount, setTotalAmount] = useState("");
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Si el emisor no responde, la página sigue sirviendo: sólo se muestra sin
    // el nombre en el encabezado.
    fetchIssuer()
      .then((issuer) => setIssuerName(issuer.name))
      .catch(() => setIssuerName(""));
  }, []);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setReceipt(null);
    try {
      setReceipt(
        await lookupReceipt({
          folio: Number(folio),
          issueDate,
          totalAmount: Number(totalAmount),
        }),
      );
    } catch (ex) {
      setError(ex instanceof Error ? ex.message : String(ex));
    } finally {
      setLoading(false);
    }
  }

  function openPrintable() {
    if (!receipt) return;
    const win = window.open("", "_blank");
    if (!win) return;
    win.document.write(decodeHtml(receipt.html_base64));
    win.document.close();
  }

  return (
    <main className="page">
      <header>
        <h1>Consulta de boletas electrónicas</h1>
        {issuerName && <p className="issuer">{issuerName}</p>}
      </header>

      <form onSubmit={onSubmit}>
        <p className="help">
          Ingresa los datos tal como aparecen en tu comprobante. Pedimos los tres
          para proteger la información de venta del comercio.
        </p>

        <label>
          Número de boleta (folio)
          <input
            type="number"
            min={1}
            required
            value={folio}
            onChange={(e) => setFolio(e.target.value)}
            placeholder="Ej: 1234"
          />
        </label>

        <label>
          Fecha de emisión
          <input
            type="date"
            required
            value={issueDate}
            onChange={(e) => setIssueDate(e.target.value)}
          />
        </label>

        <label>
          Monto total
          <input
            type="number"
            min={0}
            required
            value={totalAmount}
            onChange={(e) => setTotalAmount(e.target.value)}
            placeholder="Ej: 29800"
          />
        </label>

        <button type="submit" disabled={loading}>
          {loading ? "Buscando…" : "Buscar mi boleta"}
        </button>
      </form>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {receipt && (
        <section className="result">
          <h2>Boleta N° {receipt.folio}</h2>
          <dl>
            <dt>Fecha</dt>
            <dd>{receipt.issue_date}</dd>
            <dt>Total</dt>
            <dd>{money(receipt.total_amount)}</dd>
            <dt>Emisor</dt>
            <dd>{receipt.issuer_name}</dd>
          </dl>
          <button type="button" onClick={openPrintable}>
            Ver e imprimir
          </button>
          <iframe
            title={`Boleta ${receipt.folio}`}
            srcDoc={decodeHtml(receipt.html_base64)}
            sandbox=""
          />
        </section>
      )}
    </main>
  );
}
