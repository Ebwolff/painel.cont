import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AdminLayout } from './layouts/AdminLayout';

// Lazy-loaded pages (code-splitting per route)
const Dashboard = React.lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Upload = React.lazy(() => import('./pages/Upload').then(m => ({ default: m.Upload })));
const Alertas = React.lazy(() => import('./pages/Alertas').then(m => ({ default: m.Alertas })));
const Empresas = React.lazy(() => import('./pages/Empresas').then(m => ({ default: m.Empresas })));
const Login = React.lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const RelatorioValor = React.lazy(() => import('./pages/RelatorioValor').then(m => ({ default: m.RelatorioValor })));
const SimuladorNFe = React.lazy(() => import('./pages/SimuladorNFe').then(m => ({ default: m.SimuladorNFe })));
const Pricing = React.lazy(() => import('./pages/Pricing').then(m => ({ default: m.Pricing })));
const Users = React.lazy(() => import('./pages/Users').then(m => ({ default: m.Users })));
const MonitorFiscal = React.lazy(() => import('./pages/MonitorFiscal').then(m => ({ default: m.MonitorFiscal })));
const AdminDashboard = React.lazy(() => import('./pages/admin/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const TenantsList = React.lazy(() => import('./pages/admin/TenantsList').then(m => ({ default: m.TenantsList })));
const UsersList = React.lazy(() => import('./pages/admin/UsersList').then(m => ({ default: m.UsersList })));
const RegrasFiscais = React.lazy(() => import('./pages/admin/RegrasFiscais').then(m => ({ default: m.RegrasFiscais })));
const ClientDashboard = React.lazy(() => import('./pages/client/ClientDashboard').then(m => ({ default: m.ClientDashboard })));

const PageLoader = () => (
    <div className="min-h-[60vh] flex items-center justify-center">
        <div className="animate-spin h-8 w-8 border-2 border-end-accent border-t-transparent rounded-full" />
    </div>
);

// Protected Route Component
function RequireAuth({ children, requireAdmin = false, requireSuperAdmin = false }: { children: JSX.Element, requireAdmin?: boolean, requireSuperAdmin?: boolean }) {
    const { session, loading, isAdmin, isSuperAdmin } = useAuth();
    const location = useLocation();

    if (loading) return <div className="min-h-screen bg-end-bg flex items-center justify-center text-white">Carregando...</div>;

    if (!session) {
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    // 1. Super Admin trying to access standard routes (User Dashboard) -> Redirect to Admin Panel
    // Unless they explicitly want to see user view (not implemented yet, but good for future)
    if (!requireAdmin && !requireSuperAdmin && isSuperAdmin) {
        return <Navigate to="/admin" replace />;
    }

    // 2. Strict Super Admin Check (For /admin routes)
    if (requireSuperAdmin && !isSuperAdmin) {
        // If they are a normal admin or user trying to access Super Admin panel -> Redirect to Home
        return <Navigate to="/" replace />;
    }

    // 3. Admin Check (For Tenant Admin routes - if we had any specific ones, currently just /users which is protected by component logic/sidebar)
    // Actually, /users is inside standard layout, so users access it there. Logic is inside page.
    // If we had strict "Admin Only" pages inside the app:
    if (requireAdmin && !isAdmin) {
        return <Navigate to="/" replace />;
    }

    return children;
}

function App() {
    return (
        <AuthProvider>
            <Router>
                <Suspense fallback={<PageLoader />}>
                <Routes>
                    <Route path="/login" element={<Login />} />

                    {/* Protected Routes (User & Admin) */}
                    <Route path="/" element={
                        <RequireAuth>
                            <Layout />
                        </RequireAuth>
                    }>
                        <Route index element={<Dashboard />} />
                        <Route path="monitor" element={<MonitorFiscal />} />
                        <Route path="valor" element={<RelatorioValor />} />
                        <Route path="simulador" element={<SimuladorNFe />} />
                        <Route path="upload" element={<Upload />} />
                        <Route path="alertas" element={<Alertas />} />
                        <Route path="empresas" element={<Empresas />} />
                        <Route path="users" element={<Users />} />
                        <Route path="planos" element={<Pricing />} />
                    </Route>

                    {/* Admin Routes (Super Admin Only) */}
                    <Route path="/admin" element={
                        <RequireAuth requireSuperAdmin>
                            <AdminLayout />
                        </RequireAuth>
                    }>
                        <Route index element={<AdminDashboard />} />
                        <Route path="tenants" element={<TenantsList />} />
                        <Route path="users" element={<UsersList />} />
                        <Route path="rules" element={<RegrasFiscais />} />
                    </Route>

                    {/* Client Routes */}
                    <Route path="/client/dashboard" element={
                        <RequireAuth>
                            <ClientDashboard />
                        </RequireAuth>
                    } />

                    <Route path="*" element={<Navigate to="/" replace />} />
                </Routes>
                </Suspense>
            </Router>
        </AuthProvider>
    );
}

export default App;
