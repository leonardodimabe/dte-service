import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

export default function Layout() {
  const { user, logout } = useAuth();
  return (
    <>
      <nav className="nav">
        <strong>DTE&nbsp;Admin</strong>
        <NavLink to="/customers">Clientes</NavLink>
        {user?.role === "superadmin" && <NavLink to="/users">Usuarios</NavLink>}
        <NavLink to="/audit">Auditoría</NavLink>
        <span className="spacer" />
        <span className="muted">
          {user?.email} · {user?.role}
        </span>
        <button className="secondary" onClick={logout}>
          Salir
        </button>
      </nav>
      <div className="container">
        <Outlet />
      </div>
    </>
  );
}
