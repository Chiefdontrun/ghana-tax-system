import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";

export default function AdminLayout() {
  return (
    <div className="min-h-screen flex bg-cu-bg">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="bg-white border-b border-cu-border px-6 py-3 flex items-center justify-between shrink-0">
          <p className="text-sm font-semibold text-cu-text tracking-wide">
            DISTRICT ASSEMBLY – REVENUE UNIT
          </p>
          <span className="text-xs text-cu-muted">Administration Portal</span>
        </header>
        <main className="flex-1 p-6 overflow-y-auto" id="admin-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
