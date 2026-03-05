/**
 * Application router — defines all routes.
 * Page components are stubs in Phase 1; implemented in Phases 9 & 10.
 */

import { createBrowserRouter, RouterProvider, Navigate } from "react-router-dom";

// ── Trader pages (Phase 9) ────────────────────────────────────────────────────
import LandingPage from "@/features/trader/pages/LandingPage";
import RegisterPage from "@/features/trader/pages/RegisterPage";
import RegistrationSuccessPage from "@/features/trader/pages/RegistrationSuccessPage";
import CheckTinPage from "@/features/trader/pages/CheckTinPage";
import HelpPage from "@/features/trader/pages/HelpPage";

// ── Admin pages (Phase 10) ────────────────────────────────────────────────────
import LoginPage from "@/features/admin/pages/LoginPage";
import DashboardPage from "@/features/admin/pages/DashboardPage";
import TradersPage from "@/features/admin/pages/TradersPage";
import TraderDetailPage from "@/features/admin/pages/TraderDetailPage";
import ReportsPage from "@/features/admin/pages/ReportsPage";
import AuditLogsPage from "@/features/admin/pages/AuditLogsPage";

// ── Layouts (Phase 8) ─────────────────────────────────────────────────────────
import PublicLayout from "@/components/layout/PublicLayout";
import AdminLayout from "@/components/layout/AdminLayout";
import ProtectedRoute from "@/components/layout/ProtectedRoute";

const router = createBrowserRouter([
  // ── Public trader routes ────────────────────────────────────────────────────
  {
    element: <PublicLayout />,
    children: [
      { path: "/", element: <LandingPage /> },
      { path: "/register", element: <RegisterPage /> },
      { path: "/register/success", element: <RegistrationSuccessPage /> },
      { path: "/check-tin", element: <CheckTinPage /> },
      { path: "/help", element: <HelpPage /> },
    ],
  },
  // ── Admin login (no layout wrapper) ────────────────────────────────────────
  { path: "/admin/login", element: <LoginPage /> },
  // ── Protected admin routes ──────────────────────────────────────────────────
  {
    element: (
      <ProtectedRoute>
        <AdminLayout />
      </ProtectedRoute>
    ),
    children: [
      { path: "/admin/dashboard", element: <DashboardPage /> },
      { path: "/admin/traders", element: <TradersPage /> },
      { path: "/admin/traders/:id", element: <TraderDetailPage /> },
      { path: "/admin/reports", element: <ReportsPage /> },
      {
        path: "/admin/audit-logs",
        element: (
          <ProtectedRoute requiredRole="SYS_ADMIN">
            <AuditLogsPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
  // ── Fallback ─────────────────────────────────────────────────────────────────
  { path: "*", element: <Navigate to="/" replace /> },
]);

export default function AppRouter() {
  return <RouterProvider router={router} />;
}
