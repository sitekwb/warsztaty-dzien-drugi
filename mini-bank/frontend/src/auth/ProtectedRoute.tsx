import { Navigate, useLocation } from "react-router-dom";
import { ReactElement } from "react";
import { useAuth } from "./AuthContext";

export function ProtectedRoute({ children }: { children: ReactElement }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return null;
  if (!user) return <Navigate to="/login" state={{ from: loc }} replace />;
  return children;
}
