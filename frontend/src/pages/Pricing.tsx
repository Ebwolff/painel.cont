import React from 'react';
import { Check, ShieldCheck, Sparkles, Star, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../lib/utils';
import { api } from '../services/api';

const plans = [
    {
        id: 'starter',
        name: 'Monitor Inicial',
        price: 'R$ 499',
        description: 'Ideal para pequenos escritórios iniciando na conformidade digital.',
        features: [
            'Monitoramento de Notas (Manual)',
            'Auditoria Básica de CBS/IBS',
            'Painel de Conformidade',
            'Suporte via Email'
        ],
        icon: ShieldCheck,
        color: 'text-gray-400',
        bg: 'bg-white/5',
        button: 'Plano Atual'
    },
    {
        id: 'pro',
        name: 'Monitor Profissional',
        price: 'R$ 997',
        description: 'Automação total e visibilidade de ROI para escritórios em crescimento.',
        features: [
            'Tudo do Starter',
            'Sincronização Automática SEFAZ',
            'Calculadora de ROI Estratégico',
            'Relatórios de Valor Mensais',
            'Suporte Prioritário'
        ],
        highlight: true,
        icon: Star,
        color: 'text-blue-400',
        bg: 'bg-blue-500/5',
        button: 'Fazer Upgrade'
    },
    {
        id: 'enterprise',
        name: 'Inteligência Corporativa',
        price: 'R$ 2.490',
        description: 'A inteligência definitiva para grandes operações e consultoria estratégica.',
        features: [
            'Tudo do Pro',
            'Simulador de Reforma (IBS/CBS 2026)',
            'Detecção de Anomalias por IA',
            'Relatórios Executivos Personalizados',
            'Gerente de Conta Dedicado'
        ],
        icon: Sparkles,
        color: 'text-end-accent',
        bg: 'bg-end-accent/5',
        button: 'Falar com Consultor'
    }
];

export function Pricing() {
    const navigate = useNavigate();

    const [processingId, setProcessingId] = React.useState<string | null>(null);

    const handleAction = async (planId: string) => {
        if (planId === 'starter' || processingId) return;
        setProcessingId(planId);

        try {
            // Tenta enviar solicitação oficial ao Super Admin
            await api.post(`/features/request-upgrade?plan=${planId}`, {});
            alert(`Sua solicitação para o plano [${planId.toUpperCase()}] foi enviada com sucesso! O Super Admin será notificado para liberação.`);
            window.location.href = '/';
        } catch (error) {
            console.warn("Real request failed, falling back to demo mode", error);
            // Simulação de upgrade para a demo (Fallback)
            try {
                await api.post(`/features/set-plan?plan=${planId}`, {});
                alert(`MODO DEMO: Upgrade para [${planId.toUpperCase()}] ativado instantaneamente.`);
                window.location.href = '/';
            } catch (demoErr) {
                console.error("Failed to upgrade entirely", demoErr);
                alert("Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente em instantes.");
            }
        } finally {
            setProcessingId(null);
        }
    };

    return (
        <div className="space-y-12 pb-24 animate-in fade-in duration-700">
            <div className="text-center max-w-3xl mx-auto space-y-4">
                <h1 className="text-4xl md:text-5xl font-black text-white tracking-tighter italic">SUA CONTABILIDADE, <span className="text-end-accent text-glow">PRÓXIMO NÍVEL.</span></h1>
                <p className="text-end-text-sec text-lg">Escolha a camada de inteligência que melhor se adapta ao seu escritório e mostre valor real para seus clientes.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {plans.map((plan) => (
                    <div
                        key={plan.id}
                        className={cn(
                            "relative overflow-hidden rounded-2xl border transition-all duration-300 flex flex-col p-8",
                            plan.bg,
                            plan.highlight
                                ? "border-blue-500/50 shadow-[0_0_30px_rgba(59,130,246,0.1)] scale-105 z-10"
                                : "border-white/10 hover:border-white/20"
                        )}
                    >
                        {plan.highlight && (
                            <div className="absolute top-4 right-4">
                                <span className="bg-blue-500 text-white text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">Mais Popular</span>
                            </div>
                        )}

                        <div className="mb-8">
                            <plan.icon size={32} className={cn("mb-4", plan.color)} />
                            <h3 className="text-2xl font-black text-white tracking-tight uppercase italic">{plan.name}</h3>
                            <p className="text-sm text-end-text-sec mt-2">{plan.description}</p>
                        </div>

                        <div className="mb-8 flex items-baseline gap-1">
                            <span className="text-4xl font-black text-white">{plan.price}</span>
                            <span className="text-end-text-sec text-sm font-medium">/mês</span>
                        </div>

                        <div className="space-y-4 flex-1 mb-10">
                            {plan.features.map((feature, idx) => (
                                <div key={idx} className="flex items-start gap-3">
                                    <div className="mt-1 bg-white/10 rounded-full p-0.5">
                                        <Check size={12} className="text-end-accent" />
                                    </div>
                                    <span className="text-sm text-end-text-sec">{feature}</span>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => handleAction(plan.id)}
                            disabled={processingId !== null}
                            className={cn(
                                "w-full py-4 rounded-xl font-bold transition-all flex items-center justify-center gap-2 group",
                                plan.id === 'starter'
                                    ? "bg-white/5 text-end-text-sec cursor-default"
                                    : plan.highlight
                                        ? "bg-blue-500 text-white hover:bg-blue-600 shadow-lg shadow-blue-500/20"
                                        : "bg-end-accent text-black hover:scale-[1.02]",
                                processingId === plan.id && "opacity-50 cursor-wait"
                            )}
                        >
                            {processingId === plan.id ? 'Processando...' : plan.button}
                            {plan.id !== 'starter' && processingId !== plan.id && <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />}
                        </button>
                    </div>
                ))}
            </div>

            <div className="bg-end-card border border-end-border rounded-2xl p-8 flex flex-col md:flex-row items-center justify-between gap-8 max-w-5xl mx-auto">
                <div className="space-y-2">
                    <h4 className="text-xl font-bold text-white">Precisa de algo sob medida?</h4>
                    <p className="text-end-text-sec text-sm">Escritórios com mais de 1.000 clientes ativos possuem condições exclusivas de implementação.</p>
                </div>
                <button className="border border-white/10 hover:bg-white/5 text-white px-8 py-3 rounded-xl font-bold transition-all whitespace-nowrap">
                    CONVERSAR COM ESPECIALISTA
                </button>
            </div>
        </div>
    );
}
