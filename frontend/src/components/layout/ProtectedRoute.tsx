import { Navigate } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** If provided, user must have exactly this role (SYS_ADMIN can also access TAX_ADMIN routes) */
  requiredRole?: "SYS_ADMIN" | "TAX_ADMIN";
}

export default function ProtectedRoute({ children, requiredRole }: ProtectedRouteProps) {
  const { isAuthenticated, role } = useAuthStore();

  if (!isAuthenticated()) {
    return <Navigate to="/admin/login" replace />;
  }

  if (requiredRole === "SYS_ADMIN" && role !== "SYS_ADMIN") {
    // Only sys admins may access sys-admin-only routes
    return <Navigate to="/admin/dashboard" replace />;
  }

  if (requiredRole === "TAX_ADMIN" && role !== "TAX_ADMIN" && role !== "SYS_ADMIN") {
    // TAX_ADMIN routes also accessible to SYS_ADMIN
    return <Navigate to="/admin/login" replace />;
  }

  return <>{children}</>;
}
