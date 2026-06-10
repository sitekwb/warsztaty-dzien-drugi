import { Routes, Route, Navigate } from "react-router-dom";
import { Box, CircularProgress } from "@mui/material";
import { useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { RoleRoute } from "./auth/RoleRoute";
import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/DashboardPage";
import AccountDetailPage from "./pages/AccountDetailPage";
import TransferPage from "./pages/TransferPage";
import AgentCustomersPage from "./pages/AgentCustomersPage";
import AgentCustomerDetailPage from "./pages/AgentCustomerDetailPage";
import AgentCustomerAccountsPage from "./pages/AgentCustomerAccountsPage";
import AgentCustomerTransactionsPage from "./pages/AgentCustomerTransactionsPage";
import MyGrantsPage from "./pages/MyGrantsPage";
import ConsentsPage from "./pages/ConsentsPage";
import SupervisorQueuePage from "./pages/SupervisorQueuePage";

export default function App() {
  const { loading, user } = useAuth();
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={10}>
        <CircularProgress />
      </Box>
    );
  }
  return (
    <Routes>
      <Route
        path="/"
        element={
          <Navigate
            to={user ? (user.role === "customer" ? "/dashboard" : "/agent") : "/login"}
            replace
          />
        }
      />
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["customer"]}>
              <DashboardPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/transfer"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["customer"]}>
              <TransferPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/consents"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["customer"]}>
              <ConsentsPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/agent"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["agent", "supervisor"]}>
              <AgentCustomersPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/agent/customers/:id"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["agent", "supervisor"]}>
              <AgentCustomerDetailPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/agent/grants"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["agent", "supervisor"]}>
              <MyGrantsPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/agent/customers/:id/accounts"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["agent", "supervisor"]}>
              <AgentCustomerAccountsPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/agent/customers/:id/transactions"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["agent", "supervisor"]}>
              <AgentCustomerTransactionsPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/agent/supervisor"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["supervisor"]}>
              <SupervisorQueuePage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route
        path="/accounts/:id"
        element={
          <ProtectedRoute>
            <RoleRoute roles={["customer"]}>
              <AccountDetailPage />
            </RoleRoute>
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
