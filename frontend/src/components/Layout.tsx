import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth";

// Iconos inline (sin dependencias): trazo simple estilo "feather".
const stroke = {
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};
const IconCustomers = () => (
  <svg viewBox="0 0 24 24" {...stroke}>
    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
    <circle cx="9" cy="7" r="4" />
    <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
  </svg>
);
const IconUsers = () => (
  <svg viewBox="0 0 24 24" {...stroke}>
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
    <circle cx="12" cy="7" r="4" />
  </svg>
);
const IconAudit = () => (
  <svg viewBox="0 0 24 24" {...stroke}>
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <path d="M14 2v6h6M9 15l2 2 4-4" />
  </svg>
);

const TITLES: Record<string, string> = {
  "/customers": "Clientes",
  "/users": "Usuarios",
  "/audit": "Auditoría",
};

function titleFor(path: string): string {
  if (path.startsWith("/customers/")) return "Detalle de cliente";
  return TITLES[path] ?? "Panel";
}

export default function Layout() {
  const { user, logout } = useAuth();
  const { pathname } = useLocation();
  const initial = (user?.email ?? "?").charAt(0);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="logo">D</span>
          <span>DTE Service</span>
        </div>
        <nav>
          <div className="section">Administración</div>
          <NavLink to="/customers">
            <IconCustomers />
            <span>Clientes</span>
          </NavLink>
          {user?.role === "superadmin" && (
            <NavLink to="/users">
              <IconUsers />
              <span>Usuarios</span>
            </NavLink>
          )}
          <NavLink to="/audit">
            <IconAudit />
            <span>Auditoría</span>
          </NavLink>
        </nav>
        <div className="sidebar-footer">SII Chile · Panel de administración</div>
      </aside>

      <div className="main">
        <header className="topbar">
          <div className="page-title">{titleFor(pathname)}</div>
          <span className="spacer" />
          <div className="user">
            <span className="avatar">{initial}</span>
            <span>
              {user?.email} · {user?.role}
            </span>
          </div>
          <button className="secondary sm" onClick={logout}>
            Salir
          </button>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
