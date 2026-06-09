export interface Token {
  access_token: string;
  token_type: string;
  role: string;
  customer_id: number | null;
}

export interface Me {
  id: number;
  email: string;
  role: string;
  customer_id: number | null;
}

export interface Customer {
  id: number;
  name: string;
  key: string;
  rut: string;
  environment: string;
}

export interface ServiceInfo {
  code: string;
  name: string;
}

export interface User {
  id: number;
  email: string;
  role: string;
  customer_id: number | null;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
}

export interface RequestLog {
  id: number;
  principal_type: string;
  principal_id: number | null;
  principal_role: string | null;
  service_code: string | null;
  method: string;
  path: string;
  request_id: string;
  ip: string | null;
  status_code: number;
  outcome: string;
  latency_ms: number;
  created_at: string;
}

export interface AdminAudit {
  id: number;
  actor_user_id: number | null;
  action: string;
  target_type: string;
  target_id: string | null;
  summary: string;
  created_at: string;
}

export interface RcvDocument {
  operation: string;
  state: string;
  doc_type: number;
  folio: number;
  counterpart_rut: string;
  counterpart_name: string;
  date: string;
  exempt_amount: number;
  net_amount: number;
  vat_amount: number;
  total_amount: number;
}

export interface RcvResponse {
  issuer_rut: string;
  period: string;
  operation: string;
  count: number;
  documents: RcvDocument[];
}
