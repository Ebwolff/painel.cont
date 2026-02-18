import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Lock, Mail, ArrowRight, AlertCircle, ShieldCheck } from 'lucide-react';
import { cn } from '../lib/utils';
import { supabase } from '../lib/supabase';
import { useAuth } from '../contexts/AuthContext';

export function Login() {
    const navigate = useNavigate();
    const location = useLocation();
    const { profile } = useAuth(); // We might need to refactor this if we want to wait for profile load *after* login here locally

    // Local state because AuthContext updates might not be instant enough for immediate redirect logic inside submit
    const [loading, setLoading] = useState(false);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState<string | null>(null);

    // Get redirect path from location state or default
    const from = location.state?.from?.pathname || '/';

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const { data, error: authError } = await supabase.auth.signInWithPassword({
                email,
                password,
            });

            if (authError) {
                throw authError;
            }

            if (data.user) {
                // Fetch profile manually to decide where to go immediately
                // AuthContext will also update, but we want speed
                console.log("Login success, fetching profile for:", data.user.id);

                const { data: profileData, error: profileError } = await supabase
                    .from('profiles')
                    .select('role')
                    .eq('id', data.user.id)
                    .single();

                if (profileError) {
                    console.error("Login redirect error - Profile fetch failed:", profileError);
                } else {
                    console.log("Login profile data:", profileData);
                }

                if (profileData?.role === 'super_admin') {
                    console.log("Redirecting to Super Admin Panel...");
                    navigate('/admin');
                } else if (profileData?.role === 'monitor') {
                    console.log("Redirecting to Monitor Dashboard...");
                    navigate('/client/dashboard');
                } else {
                    console.log("Redirecting to Tenant Dashboard...");
                    navigate(from === '/login' ? '/' : from);
                }
            }
        } catch (err: any) {
            setError(err.message === 'Invalid login credentials' ? 'Email ou senha incorretos.' : err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-end-bg flex flex-col items-center justify-center p-4 relative overflow-hidden">

            {/* Background Elements */}
            <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-end-accent/5 rounded-full blur-3xl pointer-events-none" />
            <div className="absolute bottom-[-20%] left-[-10%] w-[500px] h-[500px] bg-blue-500/5 rounded-full blur-3xl pointer-events-none" />

            <div className="w-full max-w-md relative z-10">
                <div className="text-center mb-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-end-accent to-orange-600 mb-6 shadow-lg shadow-end-accent/20">
                        <ShieldCheck size={32} className="text-black" />
                    </div>
                    <h1 className="text-4xl font-black tracking-tighter text-white mb-2">
                        END <span className="text-end-accent">Monitor</span>
                    </h1>
                    <p className="text-end-text-sec text-lg">Inteligência Contábil Avançada</p>
                </div>

                <div className="bg-end-card/50 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-100">
                    <form onSubmit={handleLogin} className="space-y-6">
                        {error && (
                            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg text-red-500 text-sm flex items-center gap-3 animate-in shake">
                                <AlertCircle size={18} />
                                {error}
                            </div>
                        )}
                        <div>
                            <label className="block text-xs font-bold text-end-text-sec uppercase mb-2 tracking-wider">Email Corporativo</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Mail className="text-end-text-sec group-focus-within:text-end-accent transition-colors" size={20} />
                                </div>
                                <input
                                    type="email"
                                    name="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="seu@email.com"
                                    autoComplete="off"
                                    className="block w-full pl-12 pr-4 py-3.5 bg-black/20 border border-white/10 rounded-xl text-white placeholder-end-text-sec/30 focus:outline-none focus:ring-2 focus:ring-end-accent/50 focus:border-end-accent transition-all"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-end-text-sec uppercase mb-2 tracking-wider">Senha de Acesso</label>
                            <div className="relative group">
                                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                    <Lock className="text-end-text-sec group-focus-within:text-end-accent transition-colors" size={20} />
                                </div>
                                <input
                                    type="password"
                                    name="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="••••••••"
                                    autoComplete="off"
                                    className="block w-full pl-12 pr-4 py-3.5 bg-black/20 border border-white/10 rounded-xl text-white placeholder-end-text-sec/30 focus:outline-none focus:ring-2 focus:ring-end-accent/50 focus:border-end-accent transition-all"
                                    required
                                />
                            </div>
                        </div>

                        <div className="flex items-center justify-between text-sm">
                            <label className="flex items-center gap-2 cursor-pointer group">
                                <div className="relative flex items-center">
                                    <input type="checkbox" className="peer h-4 w-4 rounded border-white/20 bg-black/20 text-end-accent focus:ring-end-accent focus:ring-offset-0" />
                                </div>
                                <span className="text-end-text-sec group-hover:text-white transition-colors">Lembrar-me</span>
                            </label>
                            <a href="#" className="text-end-accent hover:text-end-accent-hover font-medium transition-colors">Recuperar senha</a>
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className={cn(
                                "w-full bg-gradient-to-r from-end-accent to-orange-600 hover:to-orange-500 text-black font-black py-4 rounded-xl transition-all transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center gap-2 shadow-lg shadow-end-accent/20",
                                loading && "opacity-70 cursor-not-allowed hover:scale-100"
                            )}
                        >
                            {loading ? (
                                <span className="animate-pulse">Autenticando...</span>
                            ) : (
                                <>Acessar Plataforma <ArrowRight size={20} /></>
                            )}
                        </button>
                    </form>
                </div>

                <p className="text-center mt-8 text-sm text-end-text-sec/60">
                    &copy; 2026 END Monitor Contábil. Todos os direitos reservados.
                </p>
            </div>
        </div>
    );
}
