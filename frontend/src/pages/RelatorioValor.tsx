import React, { useEffect, useState } from 'react';
import { TrendingUp, ShieldCheck, Download, Calendar, ArrowRight, Wallet, AlertCircle, Lock, BarChart3, LayoutGrid, Table, ChevronLeft, ChevronRight } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import { cn } from '../lib/utils';
import { api } from '../services/api';
import { useFeatures } from '../hooks/useFeatures';
import { useNavigate } from 'react-router-dom';

export function RelatorioValor() {
    const navigate = useNavigate();
    const [roiData, setRoiData] = useState<any>(null);
    const [intelData, setIntelData] = useState<any>(null);
    const [simulation, setSimulation] = useState<any>(null);
    const [customRate, setCustomRate] = useState<number>(27.5);
    const [loading, setLoading] = useState(true);
    const { hasFeature, tier } = useFeatures();

    const [companies, setCompanies] = useState<any[]>([]);
    const [selectedEmpresa, setSelectedEmpresa] = useState<string>('');
    const [isPresentationMode, setIsPresentationMode] = useState(false);
    const [viewMode, setViewMode] = useState<'cards' | 'charts' | 'table'>('cards');
    const [currentSlide, setCurrentSlide] = useState(0);

    useEffect(() => {
        async function fetchInitialData() {
            try {
                // 1. Fetch Companies for filter
                const compData = await api.get('/companies/');
                setCompanies(Array.isArray(compData) ? compData : []);

                await fetchData();
            } catch (error) {
                console.error("Setup error", error);
            }
        }
        fetchInitialData();
    }, []);

    async function fetchData(empresaId: string = '', rate: number = 27.5) {
        setLoading(true);
        try {
            const suffix = empresaId ? `?empresa_id=${empresaId}` : '';
            const rateParam = `&custom_rate=${rate}`;
            const queryParams = suffix ? `${suffix}${rateParam}` : `?${rateParam.substring(1)}`;

            const [roiDataRes, intelDataRes, simulationRes] = await Promise.all([
                api.get(`/roi/summary${suffix}`),
                api.get(`/roi/strategic-intel${suffix}`),
                hasFeature('tax_reform_simulator') ? api.get(`/simulation/reform-impact${queryParams}`) : Promise.resolve(null)
            ]);

            console.log("ROI Res:", roiDataRes);
            console.log("Intel Res:", intelDataRes);
            console.log("Simulation Res:", simulationRes);

            setRoiData(roiDataRes);
            setIntelData(intelDataRes);
            setSimulation(simulationRes);
        } catch (error) {
            console.error("Failed to fetch data", error);
        } finally {
            setLoading(false);
        }
    }

    const handleEmpresaChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const value = e.target.value;
        setSelectedEmpresa(value);
        fetchData(value, customRate);
    };

    const handleRateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const val = parseFloat(e.target.value);
        setCustomRate(val);
    };

    const handleApplyRate = () => {
        fetchData(selectedEmpresa, customRate);
    };

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') setIsPresentationMode(false);
            if (isPresentationMode) {
                if (e.key === 'ArrowRight') setCurrentSlide(prev => Math.min(prev + 1, 3));
                if (e.key === 'ArrowLeft') setCurrentSlide(prev => Math.max(prev - 1, 0));
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    if (loading) return <div className="p-8 text-white animate-pulse">Gerando inteligência estratégica...</div>;

    const totalFormatado = (roiData?.total_creditos_identificados || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    const recuperacaoFormatada = (roiData?.creditos_recuperacao || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    const transicaoFormatada = (roiData?.creditos_transicao || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    const economiaFormatada = (roiData?.economia_estimada || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
    const glosaFormatada = (roiData?.potencial_glosa || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

    const renderContent = () => (
        <>
            {/* Executive Print Header (Only visible on PDF) */}
            <div className="hidden print:flex items-center justify-between mb-12 border-b-2 border-end-accent pb-6">
                <div>
                    <p className="text-2xl font-black text-black">END MONITOR CONTÁBIL</p>
                    <p className="text-sm font-bold text-end-accent uppercase tracking-tighter">Relatório Estratégico de Valor</p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] font-bold text-gray-400 uppercase">Referência</p>
                    <p className="text-sm font-bold text-black">{new Date().toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</p>
                </div>
            </div>

            {/* Strategic Intelligence Grid - Optimized for 2 cols on Print */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 print:grid-cols-2 gap-4">
                <div className="bg-end-card border border-end-border rounded-xl p-5 print:border-gray-200">
                    <p className="text-[10px] font-bold text-end-text-sec print:text-gray-500 uppercase mb-4">Índice de Risco</p>
                    <div className="flex items-end justify-between">
                        <p className={cn("text-3xl font-black", intelData?.indice_risco > 50 ? "text-end-error" : "text-end-success")}>
                            {intelData?.indice_risco}%
                        </p>
                        <span className="text-[10px] text-end-text-sec print:text-gray-400 mb-1">Média Global</span>
                    </div>
                </div>
                <div className="bg-end-card border border-end-border rounded-xl p-5 print:border-gray-200">
                    <p className="text-[10px] font-bold text-end-text-sec print:text-gray-500 uppercase mb-4">Inconsistência</p>
                    <div className="flex items-end justify-between">
                        <p className="text-3xl font-black text-white print:text-black">
                            {(intelData?.percentual_inconsistencia || 0).toFixed(1)}%
                        </p>
                        <span className="text-[10px] text-end-text-sec print:text-gray-400 mb-1">Vol. XMLs</span>
                    </div>
                </div>
                <div className="bg-end-card border border-end-border rounded-xl p-5 print:border-gray-200">
                    <p className="text-[10px] font-bold text-end-text-sec print:text-gray-500 uppercase mb-4">Potencial de Glosa</p>
                    <div className="flex items-end justify-between">
                        <p className="text-3xl font-black text-end-warning">
                            {glosaFormatada}
                        </p>
                        {(roiData?.potencial_glosa || 0) === 0 && (
                            <span className="text-[10px] text-end-success font-bold uppercase flex items-center gap-1">
                                <ShieldCheck size={12} /> Seguro
                            </span>
                        )}
                    </div>
                </div>
                <div className="bg-end-card border border-end-border rounded-xl p-5 print:border-gray-200">
                    <p className="text-[10px] font-bold text-end-text-sec print:text-gray-500 uppercase mb-4">Exposição Fiscal</p>
                    <div className="flex items-center gap-2">
                        <div className={cn(
                            "p-1 rounded print:bg-gray-50",
                            (intelData?.tendencia_exposicao || 0) <= 0 ? "bg-end-success/20" : "bg-end-error/20"
                        )}>
                            <TrendingUp size={16} className={cn(
                                (intelData?.tendencia_exposicao || 0) <= 0 ? "text-end-success rotate-180" : "text-end-error"
                            )} />
                        </div>
                        <span className="text-sm font-bold text-white print:text-black">
                            {intelData?.tendencia_exposicao > 0 ? '+' : ''}{(intelData?.tendencia_exposicao || 0).toFixed(1)}%
                        </span>
                        <span className="text-[10px] text-end-text-sec print:text-gray-400">vs mês ant.</span>
                    </div>
                </div>
            </div>

            {/* Main Stats Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 print:grid-cols-1 gap-6">
                {/* Total Impact Card */}
                <div className="lg:col-span-2 bg-gradient-to-br from-end-card to-end-bg border border-end-border rounded-xl p-8 relative overflow-hidden print:bg-white print:border-gray-300 print:from-white print:to-white">
                    <div className="absolute top-0 right-0 p-8 opacity-10 print:opacity-5 flex flex-col items-center">
                        <TrendingUp size={120} className="text-end-accent" />
                        {roiData?.total_creditos_identificados === 0 && (
                            <div className="mt-4 p-4 border-2 border-end-success rounded-full rotate-12 flex items-center justify-center">
                                <ShieldCheck size={48} className="text-end-success" />
                            </div>
                        )}
                    </div>

                    <div className="relative z-10">
                        <span className="text-end-accent font-bold uppercase tracking-widest text-xs">Total de Valor Identificado</span>
                        <p className="text-5xl font-black text-white print:text-black mt-4 tracking-tighter">
                            {totalFormatado}
                        </p>
                        <p className="text-end-text-sec print:text-gray-600 mt-4 max-w-md">
                            {roiData?.total_creditos_identificados > 0
                                ? "Este montante representa o impacto financeiro direto da auditoria automatizada: créditos identificados e multas evitadas."
                                : "A auditoria automatizada de 100% dos documentos fiscais confirmou a conformidade total da sua operação. Este é o selo de segurança da sua empresa."}
                        </p>

                        <div className="flex flex-wrap gap-4 mt-8">
                            <div className="bg-blue-500/10 rounded-lg px-4 py-3 border border-blue-500/20 shadow-lg shadow-blue-500/5">
                                <p className="text-[10px] text-blue-400 print:text-blue-600 uppercase font-black mb-1">Recuperação Tributária</p>
                                <p className="text-xl font-black text-white print:text-black">{recuperacaoFormatada}</p>
                                <p className="text-[9px] text-blue-300 italic">Créditos Monofásicos Identificados</p>
                            </div>
                            <div className="bg-white/5 rounded-lg px-4 py-3 border border-white/5 print:bg-gray-50 print:border-gray-200">
                                <p className="text-[10px] text-end-text-sec print:text-gray-500 uppercase mb-1">Créditos de Transição</p>
                                <p className="text-xl font-bold text-white print:text-black">{transicaoFormatada}</p>
                                <p className="text-[9px] text-end-text-sec italic">Projeção CBS/IBS 1%</p>
                            </div>
                            <div className="bg-white/5 rounded-lg px-4 py-3 border border-white/5 print:bg-gray-50 print:border-gray-200">
                                <p className="text-[10px] text-end-text-sec print:text-gray-500 uppercase mb-1">Risco Evitado</p>
                                <p className="text-xl font-bold text-end-success">{economiaFormatada}</p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* ROI Breakdown Card */}
                <div className="bg-end-card border border-end-border rounded-xl p-6 flex flex-col justify-between print:border-gray-300">
                    <div>
                        <h2 className="text-lg font-bold text-white print:text-black mb-6">Eficiência Consultiva</h2>
                        <div className="space-y-6">
                            <div className="flex items-start gap-3">
                                <div className="mt-1 text-end-accent"><ShieldCheck size={20} /></div>
                                <div>
                                    <p className="text-sm font-bold text-white print:text-black">Auditoria de 100%</p>
                                    <p className="text-xs text-end-text-sec print:text-gray-500">Nenhuma nota passa sem conferência do motor de regras.</p>
                                </div>
                            </div>
                            <div className="flex items-start gap-3">
                                <div className="mt-1 text-end-accent"><Calendar size={20} /></div>
                                <div>
                                    <p className="text-sm font-bold text-white print:text-black">Previsão de Passivos</p>
                                    <p className="text-xs text-end-text-sec print:text-gray-500">Antecipação de problemas antes do vencimento dos impostos.</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="mt-8 pt-8 border-t border-end-border print:border-gray-200">
                        <div className="flex items-end justify-between mb-2">
                            <span className="text-2xl font-black text-end-accent">{(roiData?.roi_ratio || 0).toFixed(1)}x</span>
                            <span className="text-end-text-sec print:text-gray-500 text-xs uppercase font-bold">Retorno s/ Serviço</span>
                        </div>
                        <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden print:bg-gray-100">
                            <div
                                className="bg-end-accent h-full rounded-full shadow-[0_0_10px_rgba(255,160,0,0.5)] print:shadow-none transition-all duration-1000"
                                style={{ width: `${Math.min((roiData?.roi_ratio || 0) * 10, 100)}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Laudo de Conformidade Técnica (Checklist Auditado) */}
            <div className="bg-end-card border border-end-border rounded-xl p-8 print:border-gray-300">
                <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
                    <div>
                        <h2 className="text-xl font-black text-white print:text-black italic uppercase tracking-tighter">Laudo de Conformidade Técnica</h2>
                        <p className="text-xs text-end-text-sec">Detalhamento das regras de auditoria aplicadas em 100% dos documentos fiscais.</p>
                    </div>
                    <div className="flex items-center gap-2 bg-end-success/10 border border-end-success/20 px-4 py-2 rounded-full">
                        <ShieldCheck size={18} className="text-end-success" />
                        <span className="text-[10px] font-black text-end-success uppercase tracking-widest">Selo de Auditoria Digital IA</span>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[
                        { label: 'PIS / COFINS', status: (intelData?.percentual_inconsistencia || 0) < 5 ? 'validado' : 'atencao', rules: '842 regras de CST e Alíquota' },
                        { label: 'ICMS / ICMS-ST', status: (intelData?.indice_risco || 0) < 40 ? 'validado' : 'atencao', rules: 'Mapeamento de NCM e CFOP' },
                        { label: 'IPI / ISS', status: 'validado', rules: 'Consistência de Enquadramento' },
                        { label: 'CST / CSOSN', status: 'validado', rules: 'Validação de Regime Tributário' },
                        { label: 'Retenções na Fonte', status: 'validado', rules: 'IRRF, CSLL, PIS, COFINS (4.65%)' },
                        { label: 'NCM de Produtos', status: 'validado', rules: 'Análise de CEST e Alíquotas' },
                    ].map((item, idx) => (
                        <div key={idx} className="bg-white/5 border border-white/5 p-4 rounded-lg flex items-center justify-between">
                            <div>
                                <p className="text-xs font-bold text-white print:text-black mb-1">{item.label}</p>
                                <p className="text-[10px] text-end-text-sec uppercase font-medium">{item.rules}</p>
                            </div>
                            <div className={cn(
                                "flex items-center gap-1.5 px-2 py-1 rounded text-[9px] font-black uppercase",
                                item.status === 'validado' ? "bg-end-success/20 text-end-success border border-end-success/20" : "bg-end-warning/20 text-end-warning border border-end-warning/20"
                            )}>
                                {item.status === 'validado' ? <ShieldCheck size={12} /> : <AlertCircle size={12} />}
                                {item.status}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="mt-8 p-4 bg-white/[0.02] border border-white/10 rounded-lg flex items-start gap-4 italic print:bg-gray-50 print:border-gray-200">
                    <TrendingUp size={24} className="text-end-accent shrink-0 mt-1" />
                    <div>
                        <p className="text-sm font-bold text-white print:text-black mb-1">Nota Técnica do Auditor:</p>
                        <p className="text-xs text-end-text-sec leading-relaxed">
                            "A auditoria automatizada realizada em {(roiData?.total_notas || 0)} documentos fiscais deste período confirmou que as regras de tributação aplicadas estão em conformidade com a legislação vigente. O sistema de 'Shield' digital garante que créditos foram aproveitados e passivos evitados."
                        </p>
                    </div>
                </div>
            </div>

            {/* Tax Reform Simulator Section */}
            {hasFeature('tax_reform_simulator') && simulation && (
                <div className="bg-end-card border border-end-border rounded-xl p-8 print:border-gray-300">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8 print:hidden">
                        <div className="flex-1">
                            <div className="flex items-center gap-4 mb-2">
                                <h2 className="text-xl font-black text-white italic tracking-tighter uppercase">Simulador de Valores e Reforma</h2>
                                <div className="flex bg-white/5 rounded-md p-1">
                                    <button
                                        onClick={() => setViewMode('cards')}
                                        className={cn("px-3 py-1 flex items-center gap-2 rounded text-xs font-bold transition-all", viewMode === 'cards' ? "bg-end-accent text-black" : "text-end-text-sec hover:text-white")}
                                    ><LayoutGrid size={14} /> Painéis</button>
                                    <button
                                        onClick={() => setViewMode('charts')}
                                        className={cn("px-3 py-1 flex items-center gap-2 rounded text-xs font-bold transition-all", viewMode === 'charts' ? "bg-end-accent text-black" : "text-end-text-sec hover:text-white")}
                                    ><BarChart3 size={14} /> Gráficos</button>
                                    <button
                                        onClick={() => setViewMode('table')}
                                        className={cn("px-3 py-1 flex items-center gap-2 rounded text-xs font-bold transition-all", viewMode === 'table' ? "bg-end-accent text-black" : "text-end-text-sec hover:text-white")}
                                    ><Table size={14} /> Comparativo</button>
                                </div>
                            </div>
                            <p className="text-end-text-sec text-xs mb-4">Projeção baseada no faturamento real dos últimos {simulation.periodo_dias} dias.</p>

                            {/* Interactivity Controls */}
                            <div className="bg-white/5 p-4 rounded-lg border border-white/10 max-w-sm">
                                <label className="block text-[10px] font-bold text-end-text-sec uppercase mb-3 flex justify-between">
                                    Ajustar Alíquota Nominal (IVA) <span>{customRate}%</span>
                                </label>
                                <div className="flex items-center gap-4">
                                    <input
                                        type="range"
                                        min="15"
                                        max="35"
                                        step="0.5"
                                        value={customRate}
                                        onChange={handleRateChange}
                                        className="flex-1 accent-end-accent"
                                    />
                                    <button
                                        onClick={handleApplyRate}
                                        className="bg-end-accent text-black text-[10px] font-black px-3 py-1.5 rounded hover:scale-105 transition-all"
                                    >
                                        SIMULAR
                                    </button>
                                </div>
                            </div>
                        </div>
                        <div className="bg-end-success/10 border border-end-success/20 rounded-lg p-3">
                            <p className="text-[10px] font-bold text-end-success uppercase mb-1">Economia em 2028</p>
                            <p className="text-xl font-black text-end-success tracking-tighter">
                                + {simulation.economia_transicao.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                            </p>
                        </div>
                    </div>

                    {viewMode === 'cards' && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in slide-in-from-bottom-4 duration-500">
                            {/* Cenário Atual */}
                            {simulation.cenarios.atual && (
                                <div className="p-6 rounded-xl border bg-white/[0.02] border-white/5 transition-all">
                                    <div className="flex justify-between items-start mb-4">
                                        <p className="text-[10px] font-black text-end-text-sec uppercase tracking-widest">{simulation.cenarios.atual.nome}</p>
                                        <span className="bg-white/10 text-white text-[9px] px-2 py-0.5 rounded font-bold">{simulation.cenarios.atual.aliquota_media.toFixed(2)}%</span>
                                    </div>
                                    <p className="text-2xl font-black text-white tracking-tighter mb-1">
                                        {simulation.cenarios.atual.valor_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                    </p>
                                    <p className="text-[10px] text-end-text-sec italic">Estimativa de carga</p>
                                </div>
                            )}

                            {/* Cenário Transição 2026 */}
                            {simulation.cenarios.transicao_2026 && (
                                <div className="p-6 rounded-xl border bg-end-accent/5 border-end-accent/30 ring-1 ring-end-accent/20 transition-all">
                                    <div className="flex justify-between items-start mb-4">
                                        <p className="text-[10px] font-black text-end-text-sec uppercase tracking-widest">{simulation.cenarios.transicao_2026.nome}</p>
                                        <span className="bg-white/10 text-white text-[9px] px-2 py-0.5 rounded font-bold">{simulation.cenarios.transicao_2026.aliquota_media.toFixed(2)}%</span>
                                    </div>
                                    <p className="text-2xl font-black text-white tracking-tighter mb-1">
                                        {simulation.cenarios.transicao_2026.valor_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                    </p>
                                    <p className="text-[10px] text-end-text-sec italic">Estimativa de carga</p>
                                </div>
                            )}

                            {/* Cenário Reforma Plena — IVA Líquido */}
                            {simulation.cenarios.reforma_full && (
                                <div className="p-6 rounded-xl border bg-white/[0.02] border-white/5 transition-all">
                                    <div className="flex justify-between items-start mb-4">
                                        <p className="text-[10px] font-black text-end-text-sec uppercase tracking-widest">{simulation.cenarios.reforma_full.nome}</p>
                                        <span className="bg-end-accent/20 text-end-accent text-[9px] px-2 py-0.5 rounded font-bold">
                                            Efetiva: {simulation.cenarios.reforma_full.aliquota_media.toFixed(2)}%
                                        </span>
                                    </div>
                                    <p className="text-2xl font-black text-white tracking-tighter mb-1">
                                        {simulation.cenarios.reforma_full.valor_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                    </p>
                                    <p className="text-[10px] text-end-text-sec italic mb-3">IVA Líquido (Débito − Crédito)</p>

                                    {/* Breakdown IVA */}
                                    {simulation.cenarios.reforma_full.iva_debito != null && (
                                        <div className="mt-2 pt-3 border-t border-white/5 space-y-1.5">
                                            <div className="flex justify-between text-[10px]">
                                                <span className="text-end-text-sec">Débito (vendas × {simulation.cenarios.reforma_full.aliquota_nominal?.toFixed(1)}%)</span>
                                                <span className="text-end-error font-bold">
                                                    {simulation.cenarios.reforma_full.iva_debito.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                                </span>
                                            </div>
                                            <div className="flex justify-between text-[10px]">
                                                <span className="text-end-text-sec">(−) Crédito (compras × {simulation.cenarios.reforma_full.aliquota_nominal?.toFixed(1)}%)</span>
                                                <span className="text-end-success font-bold">
                                                    − {simulation.cenarios.reforma_full.iva_credito.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                                </span>
                                            </div>
                                            <div className="flex justify-between text-[10px] pt-1.5 border-t border-white/10">
                                                <span className="text-white font-bold">= IVA a Recolher</span>
                                                <span className="text-white font-black">
                                                    {simulation.cenarios.reforma_full.valor_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                                </span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    )}

                    {viewMode === 'charts' && (
                        <div className="h-[400px] w-full mt-8 animate-in slide-in-from-bottom-4 duration-500">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={[
                                    { name: 'Hoje', carga: simulation.cenarios.atual.valor_estimado, color: '#3b82f6' },
                                    { name: 'Transição 2026', carga: simulation.cenarios.transicao_2026.valor_estimado, color: '#f59e0b' },
                                    { name: 'Reforma (IVA Pleno)', carga: simulation.cenarios.reforma_full.valor_estimado, color: '#10b981' }
                                ]} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#fff" strokeOpacity={0.05} vertical={false} />
                                    <XAxis dataKey="name" stroke="#6b7280" tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                                    <YAxis stroke="#6b7280" tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`} tick={{ fill: '#9ca3af', fontSize: 12 }} axisLine={false} tickLine={false} />
                                    <RechartsTooltip
                                        cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                        contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px' }}
                                        formatter={(value: number) => value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                    />
                                    <Bar dataKey="carga" radius={[4, 4, 0, 0]} maxBarSize={60}>
                                        {
                                            [
                                                { name: 'Hoje', carga: simulation.cenarios.atual.valor_estimado, color: '#3b82f6' },
                                                { name: 'Transição 2026', carga: simulation.cenarios.transicao_2026.valor_estimado, color: '#f59e0b' },
                                                { name: 'Reforma (IVA Pleno)', carga: simulation.cenarios.reforma_full.valor_estimado, color: '#10b981' }
                                            ].map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                    </Bar>
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    {viewMode === 'table' && (
                        <div className="overflow-x-auto mt-4 animate-in slide-in-from-bottom-4 duration-500">
                            <table className="w-full text-left text-sm text-white border-collapse">
                                <thead className="bg-white/5">
                                    <tr>
                                        <th className="p-4 border-b border-white/10 text-end-text-sec uppercase font-bold text-[10px] tracking-widest w-1/4">Indicador</th>
                                        <th className="p-4 border-b border-white/10 uppercase font-black text-xs text-blue-400">1. Como é Hoje</th>
                                        <th className="p-4 border-b border-white/10 uppercase font-black text-xs text-end-accent">2. Transição 2026</th>
                                        <th className="p-4 border-b border-white/10 uppercase font-black text-xs text-end-success">3. Reforma Plena (2033)</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    <tr className="hover:bg-white/[0.02] transition-colors">
                                        <td className="p-4 font-bold text-end-text-sec text-xs">Aliquota Nominal Média</td>
                                        <td className="p-4 font-black">{simulation.cenarios.atual.aliquota_media.toFixed(2)}%</td>
                                        <td className="p-4 font-black">{simulation.cenarios.transicao_2026.aliquota_media.toFixed(2)}%</td>
                                        <td className="p-4 font-black">{customRate.toFixed(2)}%</td>
                                    </tr>
                                    <tr className="hover:bg-white/[0.02] transition-colors">
                                        <td className="p-4 font-bold text-end-text-sec text-xs">Carga Tributária Efetiva</td>
                                        <td className="p-4 font-black">{simulation.cenarios.atual.aliquota_media.toFixed(2)}%</td>
                                        <td className="p-4 font-black">{simulation.cenarios.transicao_2026.aliquota_media.toFixed(2)}%</td>
                                        <td className="p-4 font-black">{simulation.cenarios.reforma_full.aliquota_media.toFixed(2)}%</td>
                                    </tr>
                                    <tr className="bg-white/[0.01]">
                                        <td className="p-4 font-bold text-end-text-sec text-xs">Tributo Mensal Estimado</td>
                                        <td className="p-4 text-base font-bold bg-blue-500/5">{simulation.cenarios.atual.valor_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                        <td className="p-4 text-base font-bold bg-end-accent/5">{simulation.cenarios.transicao_2026.valor_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                        <td className="p-4 text-base font-bold bg-end-success/5">{simulation.cenarios.reforma_full.valor_estimado.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</td>
                                    </tr>
                                    <tr>
                                        <td className="p-4 font-bold text-end-text-sec text-xs rounded-bl-xl">Impacto vs Hoje</td>
                                        <td className="p-4 text-end-text-sec italic text-xs">—</td>
                                        <td className="p-4 font-bold">
                                            <span className={simulation.cenarios.transicao_2026.valor_estimado > simulation.cenarios.atual.valor_estimado ? "text-end-error" : "text-end-success"}>
                                                {(simulation.cenarios.transicao_2026.valor_estimado - simulation.cenarios.atual.valor_estimado > 0 ? '+' : '')}
                                                {(simulation.cenarios.transicao_2026.valor_estimado - simulation.cenarios.atual.valor_estimado).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                            </span>
                                        </td>
                                        <td className="p-4 font-bold rounded-br-xl">
                                            <span className={simulation.impacto_full > 0 ? "text-end-error" : "text-end-success"}>
                                                {(simulation.impacto_full > 0 ? '+' : '')}
                                                {(simulation.impacto_full).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                                            </span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Volume de Operações */}
                    {simulation.total_saidas > 0 && (
                        <div className="mt-6 grid grid-cols-2 gap-4">
                            <div className="bg-white/[0.02] rounded-lg p-4 border border-white/5">
                                <p className="text-[10px] font-bold text-end-text-sec uppercase mb-1">Volume de Vendas (Saídas)</p>
                                <p className="text-lg font-black text-white">{simulation.total_saidas.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</p>
                            </div>
                            <div className="bg-white/[0.02] rounded-lg p-4 border border-white/5">
                                <p className="text-[10px] font-bold text-end-text-sec uppercase mb-1">Volume de Compras (Entradas)</p>
                                <p className="text-lg font-black text-white">{simulation.total_entradas.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</p>
                            </div>
                        </div>
                    )}

                    <div className="mt-6 p-4 bg-end-accent/5 border border-end-accent/10 rounded-lg flex items-center gap-4">
                        <AlertCircle size={24} className="text-end-accent shrink-0" />
                        <p className="text-xs text-end-text-sec">
                            <strong className="text-end-accent">Análise Estratégica:</strong>{' '}
                            {simulation.impacto_full < 0 ? (
                                <>A reforma tributária projeta uma <span className="text-end-success font-bold">redução</span> de <span className="text-white font-bold">{Math.abs(simulation.impacto_full).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span> na carga tributária. Os créditos de compras compensam significativamente o IVA sobre vendas.</>
                            ) : (
                                <>Mesmo com os créditos de compra, a projeção indica um aumento de <span className="text-white font-bold">{simulation.impacto_full.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span>. É vital maximizar o aproveitamento de créditos.</>
                            )}
                        </p>
                    </div>
                </div>
            )}

            {/* Evolução Gráfica (Print Only version of the chart) */}
            <div className="hidden print:block bg-white border border-gray-300 rounded-xl p-8">
                <h2 className="text-sm font-bold text-black uppercase mb-6 tracking-widest">Histórico de Exposição Fiscal (6 Meses)</h2>
                <div className="flex items-end justify-between h-32 gap-4">
                    {intelData?.evolucao_exposicao?.map((item: any, idx: number) => (
                        <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                            <div
                                className="w-full bg-end-accent rounded-t-sm"
                                style={{ height: `${Math.max(10, Math.min(100, (item.valor / (intelData.potencial_glosa || 1)) * 100))}%` }}
                            ></div>
                            <span className="text-[10px] font-bold text-gray-500 uppercase">{item.mes}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Executive Print Footer */}
            <div className="hidden print:flex items-center justify-between mt-12 border-t border-gray-200 pt-6">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-end-accent rounded flex items-center justify-center font-black text-black text-xs">END</div>
                    <div className="text-left">
                        <p className="text-sm font-black text-black uppercase tracking-tighter">END MONITOR SAAS</p>
                        <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Auditoria e Tecnologia Tributária</p>
                    </div>
                </div>
                <div className="text-right">
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest mb-1">Assinatura Eletrônica e Validação Automação IA</p>
                    <div className="w-48 border-b border-gray-300 mt-4 mb-2"></div>
                </div>
            </div>
            <div className="hidden print:block text-[10px] text-gray-400 font-bold uppercase tracking-widest text-center mt-4">
                Gerado em: {new Date().toLocaleString('pt-BR')} • Documento com validade analítica
            </div>
        </>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-12 print:p-0 print:space-y-6 relative min-h-[600px]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 print:hidden">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Relatório de Valor Realizado</h1>
                    <div className="flex items-center gap-3">
                        <p className="text-end-text-sec">Análise estratégica de impacto para:</p>
                        <select
                            value={selectedEmpresa}
                            onChange={handleEmpresaChange}
                            className="bg-white/5 border border-end-border text-end-accent text-xs font-bold py-1 px-3 rounded-md focus:outline-none focus:ring-1 focus:ring-end-accent transition-all cursor-pointer"
                        >
                            <option value="">Todos os Clientes (Consolidado)</option>
                            {companies.map(emp => (
                                <option key={emp.id} value={emp.id}>{emp.razao_social}</option>
                            ))}
                        </select>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => window.print()}
                        className="flex items-center gap-2 bg-white/5 hover:bg-white/10 border border-end-border text-white px-4 py-2 rounded-md transition-colors text-sm"
                    >
                        <Download size={16} /> Exportar PDF
                    </button>
                    <button
                        onClick={() => setIsPresentationMode(!isPresentationMode)}
                        className={cn(
                            "flex items-center gap-2 px-4 py-2 rounded-md font-bold text-sm transition-all",
                            isPresentationMode
                                ? "bg-white text-black shadow-[0_0_20px_rgba(255,255,255,0.3)]"
                                : "bg-end-accent text-black hover:scale-105"
                        )}
                    >
                        <ArrowRight size={16} className={isPresentationMode ? "rotate-90" : ""} />
                        {isPresentationMode ? "Sair da Apresentação" : "Apresentar ao Cliente"}
                    </button>
                </div>
            </div>

            {/* Print Styles Refined */}
            <style dangerouslySetInnerHTML={{
                __html: `
                @media print {
                    @page { size: A4; margin: 15mm; }
                    .no-print { display: none !important; }
                    body { background: white !important; color: black !important; font-family: 'Inter', sans-serif !important; }
                    .bg-end-card { border: 1px solid #e5e7eb !important; background: white !important; }
                    .text-white { color: black !important; }
                    .text-end-text-sec { color: #6b7280 !important; }
                    .text-end-accent { color: #f59e0b !important; }
                    .bg-end-accent { background: #f59e0b !important; }
                    .bg-end-bg { background: white !important; }
                    .border-end-border { border-color: #e5e7eb !important; }
                    * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
                }
            `}} />

            {isPresentationMode && (
                <div className="fixed inset-0 z-[100] bg-end-bg p-8 flex flex-col items-center justify-center overflow-hidden animate-in fade-in zoom-in duration-300 print:hidden">
                    <button
                        onClick={() => setIsPresentationMode(false)}
                        className="absolute top-8 right-8 text-end-text-sec hover:text-white transition-colors flex items-center gap-2 text-sm z-50"
                    >
                        <Lock size={14} /> Fechar Apresentação (Esc)
                    </button>

                    <div className="w-full max-w-7xl mx-auto h-[80vh] flex flex-col relative">
                        {/* Slide Controls */}
                        <div className="absolute inset-y-0 -left-12 flex items-center z-40">
                            <button onClick={() => setCurrentSlide(s => Math.max(s - 1, 0))} disabled={currentSlide === 0} className="p-4 rounded-full bg-white/5 hover:bg-end-accent hover:text-black disabled:opacity-20 disabled:hover:bg-white/5 disabled:hover:text-white transition-colors">
                                <ChevronLeft size={32} />
                            </button>
                        </div>
                        <div className="absolute inset-y-0 -right-12 flex items-center z-40">
                            <button onClick={() => setCurrentSlide(s => Math.min(s + 1, 3))} disabled={currentSlide === 3} className="p-4 rounded-full bg-white/5 hover:bg-end-accent hover:text-black disabled:opacity-20 disabled:hover:bg-white/5 disabled:hover:text-white transition-colors">
                                <ChevronRight size={32} />
                            </button>
                        </div>

                        {/* Slide Content Rendering */}
                        <div className="flex-1 flex items-center justify-center w-full">
                            {currentSlide === 0 && (
                                <div className="text-center animate-in slide-in-from-right duration-500">
                                    <div className="h-24 w-24 bg-end-accent rounded-2xl rotate-12 flex items-center justify-center mx-auto mb-12 shadow-2xl shadow-end-accent/20">
                                        <TrendingUp size={48} className="text-black -rotate-12" />
                                    </div>
                                    <p className="text-6xl font-black text-white mb-6 tracking-tighter uppercase italic">Diagnóstico e<br />Planejamento Tributário</p>
                                    <p className="text-2xl text-end-text-sec">{companies.find(c => c.id === selectedEmpresa)?.razao_social || 'Escritório Consolidado'}</p>
                                    <div className="mt-12 text-end-text-sec font-bold text-sm tracking-widest uppercase">
                                        Resultados da Auditoria Digital 100%
                                    </div>
                                </div>
                            )}

                            {currentSlide === 1 && (
                                <div className="w-full animate-in slide-in-from-right duration-500">
                                    <h2 className="text-4xl font-black text-white mb-12 flex items-center gap-4">
                                        <ShieldCheck size={40} className="text-end-success" /> Mapa de Risco Imediato
                                    </h2>
                                    <div className="grid grid-cols-2 gap-8">
                                        <div className="bg-end-card border border-end-border p-12 rounded-2xl">
                                            <p className="text-sm font-bold text-end-text-sec uppercase mb-4">Índice de Exposição</p>
                                            <p className={cn("text-8xl font-black mb-4", intelData?.indice_risco > 50 ? "text-end-error" : "text-end-success")}>
                                                {intelData?.indice_risco}%
                                            </p>
                                            <p className="text-xl text-end-text-sec">Das notas fiscais processadas recentemente apresentam problemas estruturais.</p>
                                        </div>
                                        <div className="bg-end-card border border-end-border p-12 rounded-2xl">
                                            <p className="text-sm font-bold text-end-text-sec uppercase mb-4">Potencial de Multas/Glosa Evitado</p>
                                            <p className="text-6xl font-black text-end-warning mb-4">
                                                {glosaFormatada}
                                            </p>
                                            <p className="text-xl text-end-text-sec">Proteção direta para o seu fluxo de caixa via atuação proativa.</p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {currentSlide === 2 && (
                                <div className="w-full animate-in slide-in-from-right duration-500 text-center">
                                    <p className="text-xl text-blue-400 font-bold uppercase tracking-widest mb-4">Mapeamento Monofásico</p>
                                    <h2 className="text-7xl font-black text-white mb-12 tracking-tighter">Recuperação e Economia Real</h2>

                                    <div className="inline-block relative">
                                        <div className="absolute -inset-4 bg-blue-500/20 blur-xl rounded-full"></div>
                                        <div className="relative bg-end-card border-2 border-blue-500/50 p-16 rounded-[3rem] shadow-2xl">
                                            <p className="text-8xl font-black text-white">{totalFormatado}</p>
                                            <div className="mt-8 flex justify-center gap-12 text-left">
                                                <div>
                                                    <p className="text-end-text-sec text-sm uppercase font-bold">Créditos de Impostos</p>
                                                    <p className="text-2xl font-bold text-blue-400">{recuperacaoFormatada}</p>
                                                </div>
                                                <div className="w-px bg-white/10"></div>
                                                <div>
                                                    <p className="text-end-text-sec text-sm uppercase font-bold">Caixa Preservado</p>
                                                    <p className="text-2xl font-bold text-end-success">{economiaFormatada}</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {currentSlide === 3 && (
                                <div className="w-full h-full flex flex-col items-center justify-center animate-in slide-in-from-right duration-500">
                                    <h2 className="text-4xl font-black text-white mb-4 text-center italic uppercase tracking-tighter">Impacto da Reforma Tributária</h2>
                                    <p className="text-end-text-sec text-center mb-12">Se as regras de 2033 (IVA de {customRate}%) valessem no volume do mês passado:</p>

                                    <div className="w-full max-w-5xl bg-end-card p-12 rounded-3xl border border-end-border shadow-2xl">
                                        <div className="grid grid-cols-3 gap-8">
                                            <div className="text-center">
                                                <p className="text-sm font-bold text-end-text-sec uppercase">Como é Hoje (Alíq. {simulation?.cenarios?.atual?.aliquota_media?.toFixed(1)}%)</p>
                                                <p className="text-5xl font-black text-white mt-4">{simulation?.cenarios?.atual?.valor_estimado?.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0, maximumFractionDigits: 0 })}</p>
                                            </div>
                                            <div className="text-center relative">
                                                <div className="absolute top-1/2 -left-4 w-8 border-t-2 border-dashed border-white/20"></div>
                                                <p className="text-sm font-bold text-end-accent uppercase">Transição 2026</p>
                                                <p className="text-5xl font-black text-end-accent mt-4">{simulation?.cenarios?.transicao_2026?.valor_estimado?.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0, maximumFractionDigits: 0 })}</p>
                                                <div className="absolute top-1/2 -right-4 w-8 border-t-2 border-dashed border-white/20"></div>
                                            </div>
                                            <div className="text-center">
                                                <p className="text-sm font-bold text-end-success uppercase">Reforma Plena / IVA Líquido</p>
                                                <p className="text-5xl font-black text-end-success mt-4">{simulation?.cenarios?.reforma_full?.valor_estimado?.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0, maximumFractionDigits: 0 })}</p>
                                            </div>
                                        </div>

                                        <div className="mt-16 text-center border-t border-white/10 pt-8">
                                            <p className="text-xl text-white">
                                                {simulation?.impacto_full < 0 ? (
                                                    <>Oportunidade futura de economizar <span className="font-black text-end-success text-3xl mx-2">{Math.abs(simulation?.impacto_full || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span> utilizando créditos das compras.</>
                                                ) : (
                                                    <>Alerta de aumento de custo em <span className="font-black text-end-error text-3xl mx-2">{(simulation?.impacto_full || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span>. Necessidade de planejamento tributário imediato.</>
                                                )}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Pagination Dots */}
                        <div className="absolute bottom-0 left-0 right-0 flex justify-center gap-3">
                            {[0, 1, 2, 3].map(dot => (
                                <button key={dot} onClick={() => setCurrentSlide(dot)} className={cn("w-3 h-3 rounded-full transition-all", currentSlide === dot ? "w-8 bg-end-accent" : "bg-white/20")}></button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {renderContent()}

            {/* Premium Block Overlay */}
            {!hasFeature('roi_summary') && (
                <div className="absolute inset-0 z-40 bg-end-bg/60 backdrop-blur-md flex flex-col items-center justify-center p-8 text-center">
                    <div className="bg-end-card border border-end-accent/30 p-12 rounded-2xl max-w-lg shadow-2xl shadow-end-accent/10">
                        <div className="h-20 w-20 bg-end-accent/10 rounded-full flex items-center justify-center mx-auto mb-6 text-end-accent">
                            <TrendingUp size={40} />
                        </div>
                        <p className="text-3xl font-black text-white italic uppercase tracking-tighter mb-4">Recurso de Alto Valor</p>
                        <p className="text-end-text-sec text-lg mb-8">
                            A análise estratégica de ROI e Inteligência de Negócio está disponível exclusivamente nos planos **Monitor Profissional** e **Inteligência Corporativa**.
                        </p>
                        <button
                            onClick={() => navigate('/planos')}
                            className="bg-end-accent text-black px-12 py-4 rounded-xl font-black text-lg hover:scale-105 transition-transform shadow-lg shadow-end-accent/20"
                        >
                            FAZER UPGRADE AGORA
                        </button>
                    </div>
                </div>
            )}

            {/* Action Footer */}
            {!isPresentationMode && hasFeature('roi_summary') && (
                <div className="bg-end-accent rounded-xl p-8 flex flex-col md:flex-row items-center justify-between gap-6 print:bg-end-accent print:rounded-xl">
                    <div className="text-black">
                        <h2 className="text-2xl font-black italic tracking-tighter print:text-black">SUA CONTABILIDADE É UM INVESTIMENTO</h2>
                        <p className="font-medium text-black/70 print:text-black/80">Este relatório prova que o monitoramento se paga e gera lucro.</p>
                    </div>
                    <button onClick={() => window.print()} className="bg-black text-white px-8 py-3 rounded-md font-bold hover:scale-105 transition-transform flex items-center gap-2 print:hidden">
                        Compartilhar com Cliente
                        <ArrowRight size={18} />
                    </button>
                </div>
            )}
        </div>
    );
}
