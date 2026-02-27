import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard, UploadCloud, AlertTriangle, Building2,
    LogOut, Menu, TrendingUp, User, X, Sparkles, ShieldCheck
} from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';
import { useFeatures } from '../hooks/useFeatures';

export function Layout() {
    const location = useLocation();
    const { isAdmin, profile, signOut, hasPermission } = useAuth();
    const { usage } = useFeatures();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    // Fechar menu ao mudar de rota
    useEffect(() => {
        setIsMobileMenuOpen(false);
    }, [location.pathname]);

    const allNavItems = [
        { icon: LayoutDashboard, label: 'Dashboard', path: '/', feature: null },
        { icon: TrendingUp, label: 'Relatório de Valor', path: '/valor', feature: 'roi_summary' },
        { icon: ShieldCheck, label: 'Simulador NFe', path: '/simulador', feature: null },
        { icon: UploadCloud, label: 'Upload XML', path: '/upload', feature: 'upload_manual' },
        { icon: AlertTriangle, label: 'Alertas', path: '/alertas', feature: 'basic_monitor' },
        { icon: Building2, label: 'Empresas', path: '/empresas', feature: 'basic_monitor' },
    ];

    const navItems = allNavItems;

    if (isAdmin) {
        navItems.push({ icon: User, label: 'Equipe', path: '/users', feature: null });
    }

    return (
        <div className="flex h-screen bg-end-bg text-end-text overflow-hidden relative">
            {/* Mobile Backdrop */}
            {isMobileMenuOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={cn(
                "fixed inset-y-0 left-0 w-64 bg-end-card border-r border-end-border z-50 transform transition-transform duration-300 ease-in-out md:translate-x-0 md:static md:flex flex-col print:hidden",
                isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
            )}>
                <div className="p-6 border-b border-end-border flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold tracking-tight text-white">
                            END <span className="text-end-accent">Monitor</span>
                        </h1>
                        <p className="text-xs text-end-text-sec mt-1">Conformidade Tributária 2026</p>
                    </div>
                    <button
                        className="md:hidden p-1 text-end-text-sec hover:text-white"
                        onClick={() => setIsMobileMenuOpen(false)}
                    >
                        <X size={20} />
                    </button>
                </div>

                <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        const Icon = item.icon;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center justify-between px-3 py-2.5 rounded-md text-sm font-medium transition-colors group",
                                    isActive
                                        ? "bg-end-accent/10 text-end-accent"
                                        : "text-end-text-sec hover:bg-white/5 hover:text-white"
                                )}
                            >
                                <div className="flex items-center gap-3">
                                    <Icon size={18} />
                                    {item.label}
                                </div>

                            </Link>
                        );
                    })}
                </nav>

                {/* Usage indicator */}
                {usage && (
                    <div className="p-4 border-t border-end-border/50">
                        <div className="bg-white/5 rounded-lg p-3 border border-white/5">
                            <span className="text-[10px] font-bold text-end-text-sec uppercase tracking-widest">Empresas</span>
                            <p className="text-sm font-bold text-white mt-1">
                                {usage.companies_count} / {usage.companies_limit}
                            </p>

                            <Link
                                to="/planos"
                                className="mt-3 flex items-center justify-center gap-2 w-full py-2 bg-end-accent/10 border border-end-accent/20 text-end-accent text-[10px] font-bold uppercase rounded hover:bg-end-accent/20 transition-all group"
                            >
                                <Sparkles size={12} className="group-hover:animate-pulse" />
                                Gerenciar Plano / Upgrade
                            </Link>
                        </div>
                    </div>
                )}

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
                        <button
                            className="md:hidden p-1 text-end-text-sec hover:text-white"
                            onClick={() => setIsMobileMenuOpen(true)}
                        >
                            <Menu size={24} />
                        </button>
                        <h2 className="text-lg font-semibold text-white truncate">
                            {navItems.find(i => i.path === location.pathname)?.label || 'Bem-vindo'}
                        </h2>
                    </div>
                    <div className="flex items-center gap-3">
                        <div className="h-8 w-8 rounded-full bg-end-accent flex items-center justify-center text-black font-bold text-xs uppercase shadow-lg shadow-end-accent/20">
                            {profile?.nome?.substring(0, 2) || profile?.email?.substring(0, 2) || '??'}
                        </div>
                        <span className="text-sm text-end-text-sec hidden sm:block">
                            {profile?.nome || 'Usuário'}
                        </span>
                    </div>
                </header>

                <main className="flex-1 overflow-auto p-4 md:p-8 scroll-smooth print:p-0 print:overflow-visible">
                    <div className="max-w-6xl mx-auto space-y-6 print:max-w-none">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
}
