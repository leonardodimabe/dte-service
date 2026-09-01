/**
 * Cliente del endpoint público de consulta de boletas.
 *
 * No hay credenciales: quien consulta es el comprador, con el papel en la mano.
 * El único parámetro de configuración es a qué emisor pertenece este sitio.
 */

/** RUT del emisor cuyas boletas publica este sitio. Se fija al desplegar. */
export const ISSUER_RUT = import.meta.env.VITE_ISSUER_RUT ?? "";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

export type Issuer = { rut: string; name: string };

export type Receipt = {
  folio: number;
  doc_type: number;
  issue_date: string;
  total_amount: number;
  issuer_name: string;
  html_base64: string;
};

export class LookupError extends Error {}

async function parse<T>(response: Response): Promise<T> {
  if (response.ok) return (await response.json()) as T;

  // El backend responde con {detail} de FastAPI o con {error:{message}}.
  let message = "No pudimos completar la consulta. Intenta de nuevo.";
  try {
    const body = await response.json();
    message = body?.detail ?? body?.error?.message ?? message;
  } catch {
    /* respuesta sin cuerpo JSON: se queda el mensaje genérico */
  }
  if (response.status === 429) {
    message = "Demasiadas consultas seguidas. Espera un minuto e intenta otra vez.";
  }
  throw new LookupError(message);
}

export async function fetchIssuer(): Promise<Issuer> {
  return parse<Issuer>(await fetch(`${BASE}/public/issuer/${ISSUER_RUT}`));
}

export async function lookupReceipt(input: {
  folio: number;
  issueDate: string;
  totalAmount: number;
}): Promise<Receipt> {
  const response = await fetch(`${BASE}/public/boletas/lookup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      rut: ISSUER_RUT,
      folio: input.folio,
      issue_date: input.issueDate,
      total_amount: input.totalAmount,
    }),
  });
  return parse<Receipt>(response);
}

/** Decodifica el HTML de la boleta, que viaja en base64 (UTF-8). */
export function decodeHtml(base64: string): string {
  const bytes = Uint8Array.from(atob(base64), (c) => c.charCodeAt(0));
  return new TextDecoder("utf-8").decode(bytes);
}
