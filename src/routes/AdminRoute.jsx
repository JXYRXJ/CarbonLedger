import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext.jsx";

export default function AdminRoute() {
  const { user, isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user?.role !== "ADMIN") return <Navigate to="/unauthorized" replace />;
  return <Outlet />;
}