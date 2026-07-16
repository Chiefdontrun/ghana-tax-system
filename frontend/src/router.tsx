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
import TraderLoginPage from "@/features/trader/pages/LoginPage";
import TraderVerifyOtpPage from "@/features/trader/pages/VerifyOtpPage";
import TraderDashboardPage from "@/features/trader/pages/DashboardPage";
import PayAssessmentPage from "@/features/trader/pages/PayAssessmentPage";
import ReceiptPage from "@/features/trader/pages/ReceiptPage";

// ── Admin pages (Phase 10) ────────────────────────────────────────────────────
import LoginPage from "@/features/admin/pages/LoginPage";
import VerifyOtpPage from "@/features/admin/pages/VerifyOtpPage";
import DashboardPage from "@/features/admin/pages/DashboardPage";
import TradersPage from "@/features/admin/pages/TradersPage";
import TraderDetailPage from "@/features/admin/pages/TraderDetailPage";
import ReportsPage from "@/features/admin/pages/ReportsPage";
import AuditLogsPage from "@/features/admin/pages/AuditLogsPage";
import TaxRateSchedulesPage from "@/features/admin/pages/TaxRateSchedulesPage";
import TaxPaymentsPage from "@/features/admin/pages/TaxPaymentsPage";
import TaxAssessmentExceptionsPage from "@/features/admin/pages/TaxAssessmentExceptionsPage";

// ── Layouts (Phase 8) ─────────────────────────────────────────────────────────
import PublicLayout from "@/components/layout/PublicLayout";
import AdminLayout from "@/components/layout/AdminLayout";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import TraderLayout from "@/components/layout/TraderLayout";
import ProtectedTraderRoute from "@/components/layout/ProtectedTraderRoute";

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
  // ── Trader auth (no layout wrapper) ────────────────────────────────────────
  { path: "/trader/login", element: <TraderLoginPage /> },
  { path: "/trader/verify-otp", element: <TraderVerifyOtpPage /> },
  // ── Protected trader routes ──────────────────────────────────────────────────
  {
    element: (
      <ProtectedTraderRoute>
        <TraderLayout />
      </ProtectedTraderRoute>
    ),
    children: [
      { path: "/trader/dashboard", element: <TraderDashboardPage /> },
      { path: "/trader/assessments/:id/pay", element: <PayAssessmentPage /> },
      { path: "/trader/assessments/:id/receipt", element: <ReceiptPage /> },
    ],
  },
  // ── Admin entrypoint ───────────────────────────────────────────────────────
  { path: "/admin", element: <Navigate to="/admin/dashboard" replace /> },
  // ── Admin login (no layout wrapper) ────────────────────────────────────────
  { path: "/admin/login", element: <LoginPage /> },
  { path: "/admin/verify-otp", element: <VerifyOtpPage /> },
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
      { path: "/admin/tax/assessments", element: <TaxPaymentsPage /> },
      { path: "/admin/tax/exceptions", element: <TaxAssessmentExceptionsPage /> },
      {
        path: "/admin/tax/rate-schedules",
        element: (
          <ProtectedRoute requiredRole="SYS_ADMIN">
            <TaxRateSchedulesPage />
          </ProtectedRoute>
        ),
      },
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


