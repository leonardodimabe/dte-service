import type {
  AdminAudit,
  CafInfo,
  CertificateInfo,
  Customer,
  GrantedService,
  Me,
  RcvResponse,
  RequestLog,
  ServiceInfo,
  Token,
  User,
} from "./types";

// El navegador habla con el API bajo /api (mismo sitio): así las rutas de
// navegación del SPA (/users, /audit) no colisionan con los endpoints del API.
// dev → proxy de Vite; prod → nginx. Override con VITE_API_BASE si hace falta.
const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "/api";

// La sesión vive en una cookie HttpOnly que pone el servidor; JS no la maneja.
// `credentials: "include"` hace que el navegador la envíe en cada request.
class ApiError extends Error {}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const res = await fetch(`${BASE}${path}`, { ...opts, headers, credentials: "include" });
  if (res.status === 401) {
    // /auth/* (me, login, logout) gestionan su propio estado: no redirigir aquí.
    if (!path.startsWith("/auth/")) window.location.assign("/login");
    throw new ApiError("no autenticado");
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({}) as Record<string, unknown>);
    const msg =
      (body as { error?: { message?: string } }).error?.message ??
      (body as { detail?: string }).detail ??
      `HTTP ${res.status}`;
    throw new ApiError(msg);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

function body(data: unknown): RequestInit {
  return { method: "POST", body: JSON.stringify(data) };
}

export const api = {
  login: (email: string, password: string) => req<Token>("/auth/login", body({ email, password })),
  logout: () => req<void>("/auth/logout", { method: "POST" }),
  me: () => req<Me>("/auth/me"),

  customers: () => req<Customer[]>("/admin/customers"),
  customer: (id: number) => req<Customer>(`/admin/customers/${id}`),
  createCustomer: (data: {
    name: string;
    key: string;
    rut: string;
    environment: string;
    resolution_number?: number;
    resolution_date?: string;
  }) => req<Customer>("/admin/customers", body(data)),
  services: () => req<ServiceInfo[]>("/admin/services"),
  customerServices: (id: number) => req<GrantedService[]>(`/admin/customers/${id}/services`),
  customerCerts: (id: number) => req<CertificateInfo[]>(`/admin/customers/${id}/certificates`),
  customerCafs: (id: number) => req<CafInfo[]>(`/admin/customers/${id}/cafs`),
  grant: (id: number, service_code: string, apikey: string) =>
    req(`/admin/customers/${id}/services`, body({ service_code, apikey })),
  revokeService: (id: number, code: string) =>
    req(`/admin/customers/${id}/services/${code}`, { method: "DELETE" }),
  uploadCert: (id: number, file_base64: string, password: string) =>
    req(`/admin/customers/${id}/certificate`, body({ file_base64, password })),
  uploadCaf: (id: number, xml_base64: string) =>
    req(`/admin/customers/${id}/caf`, body({ xml_base64 })),
  rcv: (id: number, period: string, operation: string) =>
    req<RcvResponse>(`/admin/customers/${id}/rcv`, body({ period, operation })),

  users: () => req<User[]>("/users"),
  createUser: (data: {
    email: string;
    password: string;
    role: string;
    customer_id: number | null;
  }) => req<User>("/users", body(data)),
  setUserActive: (id: number, is_active: boolean) =>
    req<User>(`/users/${id}/active`, { method: "PATCH", body: JSON.stringify({ is_active }) }),

  auditRequests: (params: Record<string, string>) =>
    req<RequestLog[]>(`/audit/requests?${new URLSearchParams(params)}`),
  auditChanges: () => req<AdminAudit[]>("/audit/changes"),

  async downloadAuditCsv(): Promise<void> {
    const res = await fetch(`${BASE}/audit/requests?format=csv`, {
      credentials: "include",
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "request_log.csv";
    a.click();
    URL.revokeObjectURL(url);
  },
};
