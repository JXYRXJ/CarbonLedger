import { Routes, Route, Navigate } from "react-router-dom";
import { lazy, Suspense } from "react";
import PublicLayout from "./layouts/PublicLayout.jsx";
import DashboardLayout from "./layouts/DashboardLayout.jsx";
import ProtectedRoute from "./routes/ProtectedRoute.jsx";
import AdminRoute from "./routes/AdminRoute.jsx";
import ErrorBoundary from "./components/common/ErrorBoundary.jsx";
import Spinner from "./components/common/Spinner.jsx";

const LandingPage = lazy(() => import("./pages/LandingPage.jsx"));
const LoginPage = lazy(() => import("./pages/LoginPage.jsx"));
const RegisterPage = lazy(() => import("./pages/RegisterPage.jsx"));
const DashboardPage = lazy(() => import("./pages/DashboardPage.jsx"));
const NotFound = lazy(() => import("./pages/NotFound.jsx"));
const UnauthorizedPage = lazy(() => import("./pages/UnauthorizedPage.jsx"));
const RegistriesPage = lazy(() => import("./pages/RegistriesPage.jsx"));
const RegistryDetailPage = lazy(() => import("./pages/RegistryDetailPage.jsx"));
const ProjectsPage = lazy(() => import("./pages/ProjectsPage.jsx"));
const ProjectDetailPage = lazy(() => import("./pages/ProjectDetailPage.jsx"));
const BatchesPage = lazy(() => import("./pages/BatchesPage.jsx"));
const BatchDetailPage = lazy(() => import("./pages/BatchDetailPage.jsx"));
const PortfolioPage = lazy(() => import("./pages/PortfolioPage.jsx"));
const MarketplacePage = lazy(() => import("./pages/MarketplacePage.jsx"));
const CreateListingPage = lazy(() => import("./pages/CreateListingPage.jsx"));
const OrdersPage = lazy(() => import("./pages/OrdersPage.jsx"));
const TransactionsPage = lazy(() => import("./pages/TransactionsPage.jsx"));
const RetirementsPage = lazy(() => import("./pages/RetirementsPage.jsx"));
const AnalyticsPage = lazy(() => import("./pages/AnalyticsPage.jsx"));
const WalletPage = lazy(() => import("./pages/WalletPage.jsx"));
const SettingsPage = lazy(() => import("./pages/SettingsPage.jsx"));
const AdminPage = lazy(() => import("./pages/AdminPage.jsx"));

function Fallback() {
  return (
    <div className="flex h-screen items-center justify-center">
      <Spinner />
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
    <Suspense fallback={<Fallback />}>
      <Routes>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
        <Route path="/unauthorized" element={<UnauthorizedPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/registries" element={<RegistriesPage />} />
            <Route path="/registries/:id" element={<RegistryDetailPage />} />
            <Route path="/projects" element={<ProjectsPage />} />
            <Route path="/projects/:id" element={<ProjectDetailPage />} />
            <Route path="/assets" element={<Navigate to="/batches" replace />} />
            <Route path="/batches" element={<BatchesPage />} />
            <Route path="/batches/:id" element={<BatchDetailPage />} />
            <Route path="/portfolio" element={<PortfolioPage />} />
            <Route path="/marketplace" element={<MarketplacePage />} />
            <Route path="/listings/create" element={<CreateListingPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/transactions" element={<TransactionsPage />} />
            <Route path="/retirement" element={<Navigate to="/retirements" replace />} />
            <Route path="/retirements" element={<RetirementsPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/wallet" element={<WalletPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route element={<AdminRoute />}>
              <Route path="/admin" element={<AdminPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
    </ErrorBoundary>
  );
}
