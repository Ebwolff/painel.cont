import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout } from './components/Layout';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AdminLayout } from './layouts/AdminLayout';
import { AdminDashboard } from './pages/admin/AdminDashboard';

import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { Alertas } from './pages/Alertas';
import { Empresas } from './pages/Empresas';
import { Login } from './pages/Login';
import { RelatorioValor } from './pages/RelatorioValor';
import { SimuladorNFe } from './pages/SimuladorNFe';
import { Pricing } from './pages/Pricing';

import { TenantsList } from './pages/admin/TenantsList';
import { UsersList } from './pages/admin/UsersList';
import { RegrasFiscais } from './pages/admin/RegrasFiscais';
import { Users } from './pages/Users';
import { ClientDashboard } from './pages/client/ClientDashboard';

import { MonitorFiscal } from './pages/MonitorFiscal';

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
            </Router>
        </AuthProvider>
    );
}

export default App;
