import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, UploadCloud, AlertTriangle, Building2, LogOut, Menu, TrendingUp, User } from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';

export function Layout() {
    const location = useLocation();
    const { isAdmin, profile, signOut, hasPermission } = useAuth();

    const allNavItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/', permission: null },
        { icon: TrendingUp, label: 'Relatório de Valor', path: '/valor', permission: 'can_view_roi' },
        { icon: UploadCloud, label: 'Upload XML', path: '/upload', permission: 'can_upload_xml' },
        { icon: AlertTriangle, label: 'Alertas', path: '/alertas', permission: 'can_resolve_alerts' },
        { icon: Building2, label: 'Empresas', path: '/empresas', permission: 'can_manage_companies' },
    ];

    const navItems = allNavItems.filter(item => !item.permission || hasPermission(item.permission));

    if (isAdmin) {
        navItems.push({ icon: User, label: 'Equipe', path: '/users', permission: null });
    }

    return (
        <div className="flex h-screen bg-end-bg text-end-text overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-end-card border-r border-end-border hidden md:flex flex-col print:hidden">
                <div className="p-6 border-b border-end-border">
                    <h1 className="text-xl font-bold tracking-tight text-white">
                        END <span className="text-end-accent">Monitor</span>
                    </h1>
                    <p className="text-xs text-end-text-sec mt-1">Conformidade Tributária 2026</p>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        const Icon = item.icon;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                                    isActive
                                        ? "bg-end-accent/10 text-end-accent"
                                        : "text-end-text-sec hover:bg-white/5 hover:text-white"
                                )}
                            >
                                <Icon size={18} />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-end-border">
                    <button
                        onClick={() => signOut()}
                        className="flex items-center gap-3 px-3 py-2.5 w-full rounded-md text-sm font-medium text-end-text-sec hover:bg-red-500/10 hover:text-red-500 transition-colors"
                    >
                        <LogOut size={18} />
                        Sair
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                <header className="h-16 border-b border-end-border bg-end-bg/50 backdrop-blur-sm flex items-center justify-between px-6 z-10 print:hidden">
                    <div className="flex items-center gap-4">
                        <button className="md:hidden p-1 text-end-text-sec hover:text-white">
                            <Menu size={24} />
                        </button>
                        <h2 className="text-lg font-semibold text-white">
                            {navItems.find(i => i.path === location.pathname)?.label || 'Bem-vindo'}
                        </h2>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-end-accent flex items-center justify-center text-black font-bold text-xs uppercase">
                            {profile?.nome?.substring(0, 2) || profile?.email?.substring(0, 2) || '??'}
                        </div>
                        <span className="text-sm text-end-text-sec hidden sm:block">
                            {profile?.nome || 'Usuário'}
                        </span>
                    </div>
                </header>

                <main className="flex-1 overflow-auto p-6 md:p-8 scroll-smooth print:p-0 print:overflow-visible">
                    <div className="max-w-6xl mx-auto space-y-6 print:max-w-none">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
}
