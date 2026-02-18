import React from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, Building2, LogOut, ShieldCheck } from 'lucide-react';
import { cn } from '../lib/utils';
import { useAuth } from '../contexts/AuthContext';

export function AdminLayout() {
    const { signOut, profile } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleSignOut = async () => {
        await signOut();
        navigate('/login');
    };

    const navItems = [
        { icon: LayoutDashboard, label: 'Visão Geral', path: '/admin' },
        { icon: Building2, label: 'Escritórios (Tenants)', path: '/admin/tenants' },
        { icon: Users, label: 'Usuários do Sistema', path: '/admin/users' },
    ];

    return (
        <div className="flex h-screen bg-end-bg text-white font-sans overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-black/40 border-r border-white/10 flex flex-col">
                <div className="p-6 border-b border-white/10">
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-8 h-8 rounded-lg bg-red-600 flex items-center justify-center">
                            <ShieldCheck size={18} className="text-white" />
                        </div>
                        <span className="font-black text-lg tracking-tight">SUPER ADMIN</span>
                    </div>
                    <p className="text-xs text-end-text-sec">Gestão Centralizada</p>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={cn(
                                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all group",
                                    isActive
                                        ? "bg-red-600 text-white shadow-lg shadow-red-900/20"
                                        : "text-end-text-sec hover:text-white hover:bg-white/5"
                                )}
                            >
                                <item.icon size={18} className={cn("", isActive ? "text-white" : "group-hover:text-red-500 transition-colors")} />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-white/10">
                    <div className="bg-white/5 rounded-lg p-3 mb-3">
                        <p className="text-xs font-bold text-white">{profile?.nome || 'Administrador'}</p>
                        <p className="text-[10px] text-end-text-sec truncate">{profile?.email}</p>
                    </div>
                    <button
                        onClick={handleSignOut}
                        className="flex items-center gap-2 w-full px-3 py-2 text-sm font-medium text-end-text-sec hover:text-white hover:bg-white/5 rounded-lg transition-colors"
                    >
                        <LogOut size={18} />
                        Sair do Sistema
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto bg-[url('https://grainy-gradients.vercel.app/noise.svg')] bg-opacity-20">
                <div className="p-8 max-w-7xl mx-auto">
                    <Outlet />
                </div>
            </main>
        </div>
    );
}
