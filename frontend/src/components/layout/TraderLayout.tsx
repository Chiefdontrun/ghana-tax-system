import { Outlet } from "react-router-dom";
import { useTraderAuth } from "../features/trader/hooks/useTraderAuth";
import { useTraderAuthStore } from "@/store/traderAuthStore";

export default function TraderLayout() {
  const { logout } = useTraderAuth();
  const { name } = useTraderAuthStore();

  return (
    <div className="min-h-screen flex flex-col bg-cu-bg">
      <header className="bg-cu-red text-white shadow-md flex items-center justify-between px-4 sm:px-6 py-3">
        <div className="flex-1 min-w-0">
          <p className="font-bold text-sm sm:text-base tracking-wide leading-tight">
            DISTRICT ASSEMBLY – REVENUE UNIT
          </p>
          <p className="text-white/70 text-xs">Trader Portal</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm hidden sm:inline">{name}</span>
          <button onClick={logout} className="text-sm text-white/80 hover:text-white transition-colors">
            Logout
          </button>
        </div>
      </header>
      <main className="flex-1 p-4 sm:p-6 lg:p-8" id="main-content">
        <Outlet />
      </main>
    </div>
  );
}
