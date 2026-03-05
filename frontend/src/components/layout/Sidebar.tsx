import { NavLink, useNavigate } from "react-router-dom";
import clsx from "clsx";
import { useAuthStore } from "@/store/authStore";

interface NavItem {
  to: string;
  label: string;
  icon: React.ReactNode;
  sysAdminOnly?: boolean;
}

function DashboardIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  );
}

function TradersIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function ReportsIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

function AuditIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  );
}

const NAV_ITEMS: NavItem[] = [
  { to: "/admin/dashboard", label: "Dashboard", icon: <DashboardIcon /> },
  { to: "/admin/traders", label: "Traders", icon: <TradersIcon /> },
  { to: "/admin/reports", label: "Reports", icon: <ReportsIcon /> },
  { to: "/admin/audit-logs", label: "Audit Logs", icon: <AuditIcon />, sysAdminOnly: true },
];

export default function Sidebar() {
  const { clearAuth, role, email } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    clearAuth();
    navigate("/admin/login");
  };

  return (
    <aside className="w-64 bg-white border-r border-cu-border flex flex-col h-screen sticky top-0" aria-label="Admin navigation">
      {/* Branding */}
      <div className="bg-cu-red px-5 py-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-white/20 flex items-center justify-center shrink-0">
            <svg viewBox="0 0 24 24" className="h-5 w-5 text-white" fill="currentColor">
              <polygon points="12,3 14.5,9 21,9 16,13.5 18,20 12,16 6,20 8,13.5 3,9 9.5,9" opacity="0.9" />
            </svg>
          </div>
          <div className="min-w-0">
            <p className="text-white font-bold text-xs tracking-wide leading-tight truncate">
              DA REVENUE SYSTEM
            </p>
            <p className="text-white/60 text-xs truncate">Admin Portal</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 overflow-y-auto" aria-label="Sidebar">
        <ul className="space-y-0.5">
          {NAV_ITEMS.filter((item) => !item.sysAdminOnly || role === "SYS_ADMIN").map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  clsx(
                    "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                    isActive
                      ? "bg-cu-red/10 text-cu-red border-l-4 border-cu-red pl-2"
                      : "text-cu-text hover:bg-gray-100 border-l-4 border-transparent pl-2"
                  )
                }
              >
                <span className="shrink-0">{item.icon}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* User + Logout */}
      <div className="border-t border-cu-border px-3 py-3">
        <div className="px-3 py-2 mb-2">
          <p className="text-xs font-medium text-cu-text truncate">{email || "Admin"}</p>
          <p className="text-xs text-cu-muted">{role === "SYS_ADMIN" ? "System Admin" : "Tax Admin"}</p>
        </div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 w-full px-3 py-2.5 rounded-md text-sm font-medium text-cu-muted hover:bg-red-50 hover:text-cu-red transition-colors border-l-4 border-transparent pl-2"
        >
          <LogoutIcon />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
