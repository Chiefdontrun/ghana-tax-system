import { Navigate, useLocation } from "react-router-dom";
import { useTraderAuthStore } from "@/store/traderAuthStore";

interface ProtectedTraderRouteProps {
  children: React.ReactNode;
}

export default function ProtectedTraderRoute({ children }: ProtectedTraderRouteProps) {
  const { isAuthenticated } = useTraderAuthStore();
  const location = useLocation();

  if (!isAuthenticated()) {
    // Redirect them to the /trader/login page, but save the current location they were
    // trying to go to when they were redirected. This allows us to send them
    // along to that page after they login, which is a nicer user experience
    // than dropping them off on the home page.
    return <Navigate to="/trader/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}
