import React, { useState } from 'react';
import { Check, ShieldCheck, Sparkles, Star, ArrowRight, Building2, Calculator } from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';

// Motor de pricing incremental
function calcBilling(n: number): number {
    if (n <= 0) return 0;
    if (n === 1) return 97;
    if (n <= 10) return 97 + (n - 1) * 40;
    if (n <= 50) return 97 + 9 * 40 + (n - 10) * 20;
    return 97 + 9 * 40 + 40 * 20 + (n - 50) * 10;
}

function getTier(n: number) {
    if (n <= 0) return { label: 'Sem CNPJs', color: 'text-end-text-sec', badge: 'bg-white/10' };
    if (n === 1) return { label: 'Individual', color: 'text-slate-300', badge: 'bg-slate-500/20' };
    if (n <= 10) return { label: 'Starter', color: 'text-green-400', badge: 'bg-green-500/20' };
    if (n <= 50) return { label: 'Escritório', color: 'text-blue-400', badge: 'bg-blue-500/20' };
    return { label: 'Enterprise', color: 'text-amber-400', badge: 'bg-amber-500/20' };
}

const plans = [
    {
        id: 'individual',
        name: 'Individual',
        cnpjs: '1 CNPJ',
        price: 'R$ 97',
        priceNote: 'valor fixo / mês',
        rateNote: null,
        description: 'Contador autônomo ou empresa com contabilidade própria.',
        features: [
            '1 empresa monitorada',
            'Upload de XML ilimitado',
            'Auditoria CBS/IBS automática',
            'Alertas de conformidade',
            'Painel de conformidade',
        ],
        icon: ShieldCheck,
        color: 'text-slate-300',
        bg: 'bg-white/5',
        border: 'border-white/10',
        button: 'Começar Agora',
        buttonStyle: 'bg-white/10 text-white hover:bg-white/15',
        planKey: 'starter',
    },
    {
        id: 'escritorio',
        name: 'Escritório',
        cnpjs: '2 a 50 CNPJs',
        price: null,
        priceNote: null,
        rateNote: 'Precificação progressiva por CNPJ',
        description: 'Escritórios contábeis com carteira de clientes variada.',
        features: [
            'De R$ 40 a R$ 20 por CNPJ/mês',
            'Sincronização Automática SEFAZ',
            'Calculadora de ROI Estratégico',
            'Relatório de Valor por cliente',
            'Suporte Prioritário',
        ],
        highlight: true,
        icon: Star,
        color: 'text-blue-400',
        bg: 'bg-blue-500/5',
        border: 'border-blue-500/40',
        button: 'Solicitar Upgrade',
        buttonStyle: 'bg-blue-500 text-white hover:bg-blue-600 shadow-lg shadow-blue-500/20',
        planKey: 'pro',
    },
    {
        id: 'enterprise',
        name: 'Enterprise',
        cnpjs: '51+ CNPJs',
        price: null,
        priceNote: null,
        rateNote: 'R$ 10 por CNPJ/mês a partir do 51º',
        description: 'Grandes escritórios e grupos contábeis com alta escala.',
        features: [
            'R$ 10 por CNPJ/mês excedente',
            'Simulador de Reforma Tributária 2026',
            'Detecção de Anomalias por IA',
            'Relatórios Executivos e Gerenciais',
            'Suporte + Gerente de Conta dedicado',
        ],
        icon: Sparkles,
        color: 'text-amber-400',
        bg: 'bg-amber-500/5',
        border: 'border-amber-500/20',
        button: 'Falar com Consultor',
        buttonStyle: 'bg-end-accent text-black hover:scale-[1.02]',
        planKey: 'enterprise',
    },
];

export function Pricing() {
    const [cnpjCount, setCnpjCount] = useState(5);
    const [processingId, setProcessingId] = useState<string | null>(null);

    const billing = calcBilling(cnpjCount);
    const tier = getTier(cnpjCount);

    // Escala não-linear: slider 1-300 com arrastar suave
    const sliderToCount = (val: number) => val;
    const countToSlider = (n: number) => n;

    const handleAction = async (planKey: string, planId: string) => {
        if (planId === 'individual') {
            // Individual usa o plano starter diretamente
            setProcessingId(planId);
            try {
                await api.post(`/features/request-upgrade?plan=${planKey}`, {});
                alert('Sua solicitação foi enviada! O Super Admin será notificado.');
                window.location.href = '/';
            } catch {
                try {
                    await api.post(`/features/set-plan?plan=${planKey}`, {});
                    window.location.href = '/';
                } catch { alert('Erro ao processar. Tente novamente.'); }
            } finally { setProcessingId(null); }
            return;
        }
        if (processingId) return;
        setProcessingId(planId);
        try {
            await api.post(`/features/request-upgrade?plan=${planKey}`, {});
            alert(`Solicitação para [${planId.toUpperCase()}] enviada! Aguarde liberação pelo Super Admin.`);
            window.location.href = '/';
        } catch {
            alert('Ocorreu um erro. Por favor, tente novamente.');
        } finally { setProcessingId(null); }
    };

    return (
        <div className="space-y-12 pb-24 animate-in fade-in duration-700">
            {/* Header */}
            <div className="text-center max-w-3xl mx-auto space-y-4">
                <h1 className="text-4xl md:text-5xl font-black text-white tracking-tighter italic">
                    PAGUE APENAS PELO QUE <span className="text-end-accent text-glow">VOCÊ USA.</span>
                </h1>
                <p className="text-end-text-sec text-lg">
                    Precificação progressiva por CNPJ monitorado. Quanto maior sua carteira, menor o custo por cliente.
                </p>
            </div>

            {/* Simulador Interativo */}
            <div className="max-w-2xl mx-auto bg-end-card border border-end-border rounded-2xl p-8">
                <div className="flex items-center gap-2 mb-6">
                    <Calculator size={20} className="text-end-accent" />
                    <h3 className="text-lg font-bold text-white">Simule seu valor mensal</h3>
                </div>
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <label className="text-sm text-end-text-sec font-bold uppercase tracking-wide">
                            CNPJs Monitorados
                        </label>
                        <div className="flex items-center gap-3">
                            <span className={cn("text-xs font-bold px-2 py-1 rounded uppercase", tier.badge, tier.color)}>
                                {tier.label}
                            </span>
                            <span className="text-2xl font-black text-white w-14 text-right">{cnpjCount}</span>
                        </div>
                    </div>
                    <input
                        type="range"
                        min={1}
                        max={300}
                        value={cnpjCount}
                        onChange={e => setCnpjCount(Number(e.target.value))}
                        className="w-full accent-end-accent h-2 rounded-full cursor-pointer"
                    />
                    <div className="flex justify-between text-[10px] text-end-text-sec font-bold">
                        <span>1</span><span>50</span><span>100</span><span>200</span><span>300</span>
                    </div>
                </div>

                <div className="mt-6 pt-6 border-t border-white/10 flex items-center justify-between">
                    <div>
                        <p className="text-xs text-end-text-sec uppercase font-bold">Valor Mensal Estimado</p>
                        <p className="text-4xl font-black text-white mt-1">
                            R$ {billing.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                        </p>
                        <p className="text-[10px] text-end-text-sec mt-1">
                            ≈ R$ {(billing / cnpjCount).toFixed(2)}/CNPJ • {cnpjCount} empresa{cnpjCount > 1 ? 's' : ''} monitorada{cnpjCount > 1 ? 's' : ''}
                        </p>
                    </div>
                    <div className="bg-end-accent/10 border border-end-accent/20 rounded-xl p-4 text-center">
                        <Building2 size={20} className="text-end-accent mx-auto mb-1" />
                        <p className="text-[10px] font-bold text-end-accent uppercase">ROI médio</p>
                        <p className="text-sm font-black text-white">
                            {(billing * 8).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                        </p>
                        <p className="text-[9px] text-end-text-sec">estimado em recuper.</p>
                    </div>
                </div>
            </div>

            {/* Cards de plano */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {plans.map((plan) => (
                    <div
                        key={plan.id}
                        className={cn(
                            "relative overflow-hidden rounded-2xl border transition-all duration-300 flex flex-col p-8",
                            plan.bg, plan.border,
                            plan.highlight ? "shadow-[0_0_30px_rgba(59,130,246,0.1)] scale-105 z-10" : "hover:border-white/20"
                        )}
                    >
                        {plan.highlight && (
                            <div className="absolute top-4 right-4">
                                <span className="bg-blue-500 text-white text-[10px] font-black px-3 py-1 rounded-full uppercase tracking-widest">
                                    Mais Popular
                                </span>
                            </div>
                        )}

                        <div className="mb-6">
                            <plan.icon size={28} className={cn("mb-3", plan.color)} />
                            <h3 className="text-2xl font-black text-white uppercase italic">{plan.name}</h3>
                            <div className={cn("text-xs font-bold uppercase mt-1", plan.color)}>{plan.cnpjs}</div>
                            <p className="text-sm text-end-text-sec mt-2">{plan.description}</p>
                        </div>

                        <div className="mb-8">
                            {plan.price ? (
                                <div>
                                    <div className="flex items-baseline gap-1">
                                        <span className="text-4xl font-black text-white">{plan.price}</span>
                                        <span className="text-end-text-sec text-sm">/mês</span>
                                    </div>
                                    {plan.priceNote && <p className="text-[10px] text-end-text-sec mt-1">{plan.priceNote}</p>}
                                </div>
                            ) : (
                                <div>
                                    <span className={cn("text-sm font-bold", plan.color)}>{plan.rateNote}</span>
                                    <div className="mt-2 text-end-text-sec text-xs">
                                        {plan.id === 'escritorio' && (
                                            <>2 CNPJs = <strong className="text-white">R$ 137</strong> • 10 CNPJs = <strong className="text-white">R$ 457</strong> • 50 CNPJs = <strong className="text-white">R$ 1.257</strong></>
                                        )}
                                        {plan.id === 'enterprise' && (
                                            <>51 CNPJs = <strong className="text-white">R$ 1.267</strong> • 100 CNPJs = <strong className="text-white">R$ 1.757</strong></>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>

                        <div className="space-y-3 flex-1 mb-8">
                            {plan.features.map((feature, idx) => (
                                <div key={idx} className="flex items-start gap-3">
                                    <div className="mt-0.5 bg-white/10 rounded-full p-0.5 shrink-0">
                                        <Check size={12} className="text-end-accent" />
                                    </div>
                                    <span className="text-sm text-end-text-sec">{feature}</span>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => handleAction(plan.planKey, plan.id)}
                            disabled={processingId !== null}
                            className={cn(
                                "w-full py-4 rounded-xl font-bold transition-all flex items-center justify-center gap-2 group",
                                plan.buttonStyle,
                                processingId === plan.id && "opacity-50 cursor-wait"
                            )}
                        >
                            {processingId === plan.id ? 'Processando...' : plan.button}
                            {processingId !== plan.id && (
                                <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
                            )}
                        </button>
                    </div>
                ))}
            </div>

            {/* Tabela de referência */}
            <div className="max-w-3xl mx-auto">
                <h4 className="text-center text-sm font-bold text-end-text-sec uppercase tracking-widest mb-6">Tabela de Referência de Preços</h4>
                <div className="bg-end-card border border-end-border rounded-xl overflow-hidden">
                    <table className="w-full text-sm">
                        <thead>
                            <tr className="bg-white/5 border-b border-white/10">
                                <th className="p-4 text-left text-xs font-bold text-end-text-sec uppercase">CNPJs</th>
                                <th className="p-4 text-left text-xs font-bold text-end-text-sec uppercase">Faixa</th>
                                <th className="p-4 text-right text-xs font-bold text-end-text-sec uppercase">Valor/Mês</th>
                                <th className="p-4 text-right text-xs font-bold text-end-text-sec uppercase">R$/CNPJ</th>
                            </tr>
                        </thead>
                        <tbody>
                            {[1, 5, 10, 15, 25, 50, 75, 100, 150, 200, 300, 500].map(n => {
                                const v = calcBilling(n);
                                const t = getTier(n);
                                return (
                                    <tr key={n} className="border-b border-white/5 last:border-0 hover:bg-white/5">
                                        <td className="p-4 font-mono text-white font-bold">{n}</td>
                                        <td className="p-4">
                                            <span className={cn("text-[10px] font-bold px-2 py-0.5 rounded uppercase", t.badge, t.color)}>
                                                {t.label}
                                            </span>
                                        </td>
                                        <td className="p-4 text-right text-white font-bold">
                                            R$ {v.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                                        </td>
                                        <td className="p-4 text-right text-end-text-sec text-xs">
                                            R$ {(v / n).toFixed(2)}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* CTA enterprise */}
            <div className="bg-end-card border border-end-border rounded-2xl p-8 flex flex-col md:flex-row items-center justify-between gap-8 max-w-5xl mx-auto">
                <div className="space-y-2">
                    <h4 className="text-xl font-bold text-white">Precisa de algo sob medida?</h4>
                    <p className="text-end-text-sec text-sm">
                        Escritórios com mais de 200 CNPJs possuem condições exclusivas de implementação e suporte dedicado.
                    </p>
                </div>
                <button className="border border-white/10 hover:bg-white/5 text-white px-8 py-3 rounded-xl font-bold transition-all whitespace-nowrap">
                    CONVERSAR COM ESPECIALISTA
                </button>
            </div>
        </div>
    );
}
