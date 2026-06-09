import type {
  AdminAudit,
  Customer,
  Me,
  RcvResponse,
  RequestLog,
  ServiceInfo,
  Token,
  User,
} from "./types";

const BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

let token: string | null = localStorage.getItem("token");

export function setToken(value: string | null): void {
  token = value;
  if (value) localStorage.setItem("token", value);
  else localStorage.removeItem("token");
}

export function getToken(): string | null {
  return token;
}

class ApiError extends Error {}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...opts, headers });
  if (res.status === 401) {
    setToken(null);
    if (!path.startsWith("/auth/login")) window.location.assign("/login");
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
  login: (email: string, password: string) =>
    req<Token>("/auth/login", body({ email, password })),
  me: () => req<Me>("/auth/me"),

  customers: () => req<Customer[]>("/admin/customers"),
  createCustomer: (data: Partial<Customer>) => req<Customer>("/admin/customers", body(data)),
  services: () => req<ServiceInfo[]>("/admin/services"),
  grant: (id: number, service_code: string, apikey: string) =>
    req(`/admin/customers/${id}/services`, body({ service_code, apikey })),
  uploadCert: (id: number, file_base64: string, password: string) =>
    req(`/admin/customers/${id}/certificate`, body({ file_base64, password })),
  uploadCaf: (id: number, xml_base64: string) =>
    req(`/admin/customers/${id}/caf`, body({ xml_base64 })),
  rcv: (id: number, period: string, operation: string) =>
    req<RcvResponse>(`/admin/customers/${id}/rcv`, body({ period, operation })),

  users: () => req<User[]>("/users"),
  createUser: (data: { email: string; password: string; role: string; customer_id: number | null }) =>
    req<User>("/users", body(data)),
  setUserActive: (id: number, is_active: boolean) =>
    req<User>(`/users/${id}/active`, { method: "PATCH", body: JSON.stringify({ is_active }) }),

  auditRequests: (params: Record<string, string>) =>
    req<RequestLog[]>(`/audit/requests?${new URLSearchParams(params)}`),
  auditChanges: () => req<AdminAudit[]>("/audit/changes"),

  async downloadAuditCsv(): Promise<void> {
    const res = await fetch(`${BASE}/audit/requests?format=csv`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
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
