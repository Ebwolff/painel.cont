import React, { useEffect, useState } from 'react';
import { TrendingUp, ShieldCheck, Download, Calendar, ArrowRight, Wallet, AlertCircle, Lock } from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';
import { useFeatures } from '../hooks/useFeatures';
import { useNavigate } from 'react-router-dom';

export function RelatorioValor() {
    const navigate = useNavigate();
    const [roiData, setRoiData] = useState<any>(null);
    const [intelData, setIntelData] = useState<any>(null);
    const [simulation, setSimulation] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const { hasFeature, tier } = useFeatures();

    const [companies, setCompanies] = useState<any[]>([]);
    const [selectedEmpresa, setSelectedEmpresa] = useState<string>('');
    const [isPresentationMode, setIsPresentationMode] = useState(false);

    useEffect(() => {
        async function fetchInitialData() {
            try {
                // 1. Fetch Companies for filter
                const compData = await api.get('/companies/');
                setCompanies(compData);

                await fetchData();
            } catch (error) {
                console.error("Setup error", error);
            }
        }
        fetchInitialData();
    }, []);

    async function fetchData(empresaId: string = '') {
        setLoading(true);
        try {
            const suffix = empresaId ? `?empresa_id=${empresaId}` : '';
            console.log(`Fetching RelatorioValor data for ${empresaId || 'all'}...`);

            const [roiDataRes, intelDataRes, simulationRes] = await Promise.all([
                api.get(`/roi/summary${suffix}`),
                api.get(`/roi/strategic-intel${suffix}`),
                hasFeature('tax_reform_simulator') ? api.get(`/simulation/reform-impact${suffix}`) : Promise.resolve(null)
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
        fetchData(value);
    };

    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') setIsPresentationMode(false);
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
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
                    <h1 className="text-2xl font-black text-black">END MONITOR CONTÁBIL</h1>
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
                        <h4 className={cn("text-3xl font-black", intelData?.indice_risco > 50 ? "text-end-error" : "text-end-success")}>
                            {intelData?.indice_risco}%
                        </h4>
                        <span className="text-[10px] text-end-text-sec print:text-gray-400 mb-1">Média Global</span>
                    </div>
                </div>
                <div className="bg-end-card border border-end-border rounded-xl p-5 print:border-gray-200">
                    <p className="text-[10px] font-bold text-end-text-sec print:text-gray-500 uppercase mb-4">Inconsistência</p>
                    <div className="flex items-end justify-between">
                        <h4 className="text-3xl font-black text-white print:text-black">
                            {(intelData?.percentual_inconsistencia || 0).toFixed(1)}%
                        </h4>
                        <span className="text-[10px] text-end-text-sec print:text-gray-400 mb-1">Vol. XMLs</span>
                    </div>
                </div>
                <div className="bg-end-card border border-end-border rounded-xl p-5 print:border-gray-200">
                    <p className="text-[10px] font-bold text-end-text-sec print:text-gray-500 uppercase mb-4">Potencial de Glosa</p>
                    <div className="flex items-end justify-between">
                        <h4 className="text-3xl font-black text-end-warning">
                            {glosaFormatada}
                        </h4>
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
                    <div className="absolute top-0 right-0 p-8 opacity-10 print:opacity-5">
                        <TrendingUp size={120} className="text-end-accent" />
                    </div>

                    <div className="relative z-10">
                        <span className="text-end-accent font-bold uppercase tracking-widest text-xs">Total de Valor Identificado</span>
                        <h3 className="text-5xl font-black text-white print:text-black mt-4 tracking-tighter">
                            {totalFormatado}
                        </h3>
                        <p className="text-end-text-sec print:text-gray-600 mt-4 max-w-md">
                            Este montante representa o impacto financeiro direto da auditoria automatizada: créditos identificados e multas evitadas.
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
                        <h4 className="text-lg font-bold text-white print:text-black mb-6">Eficiência Consultiva</h4>
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

            {/* Comparison Section */}
            <div className="bg-end-card border border-end-border rounded-xl overflow-hidden print:border-gray-300">
                <div className="p-6 border-b border-end-border print:border-gray-200 flex justify-between items-center">
                    <h4 className="text-lg font-bold text-white print:text-black">Demonstrativo de Valor</h4>
                    <span className="text-[10px] font-bold text-end-accent uppercase">Auditoria 100% Digital</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 print:grid-cols-2">
                    <div className="p-8 border-r border-end-border bg-white/[0.02] print:border-gray-200 print:bg-gray-50">
                        <h5 className="text-end-text-sec print:text-gray-500 font-bold uppercase text-[10px] mb-6 tracking-widest">Contabilidade Tradicional (Reativa)</h5>
                        <ul className="space-y-4">
                            <li className="flex items-center gap-3 text-sm text-end-text-sec print:text-gray-700">
                                <AlertCircle size={16} className="text-end-error" /> Conferência manual por amostragem
                            </li>
                            <li className="flex items-center gap-3 text-sm text-end-text-sec print:text-gray-700">
                                <AlertCircle size={16} className="text-end-error" /> Créditos perdidos por prazo expirado
                            </li>
                            <li className="flex items-center gap-3 text-sm text-end-text-sec print:text-gray-700">
                                <AlertCircle size={16} className="text-end-error" /> Dependência do envio do cliente
                            </li>
                        </ul>
                    </div>
                    <div className="p-8">
                        <h5 className="text-end-accent font-bold uppercase text-[10px] mb-6 tracking-widest">Modelo END Monitor (Proativo)</h5>
                        <ul className="space-y-4">
                            <li className="flex items-center gap-3 text-sm text-white print:text-black">
                                <ShieldCheck size={16} className="text-end-success" /> Conferência de 100% dos XMLs em tempo real
                            </li>
                            <li className="flex items-center gap-3 text-sm text-white print:text-black">
                                <ShieldCheck size={16} className="text-end-success" /> Aproveitamento máximo de CBS/IBS
                            </li>
                            <li className="flex items-center gap-3 text-sm text-white print:text-black">
                                <ShieldCheck size={16} className="text-end-success" /> Sincronização automática via SEFAZ
                            </li>
                        </ul>
                    </div>
                </div>
            </div>

            {/* Tax Reform Simulator Section */}
            {hasFeature('tax_reform_simulator') && simulation && (
                <div className="bg-end-card border border-end-border rounded-xl p-8 print:border-gray-300">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-8">
                        <div>
                            <h4 className="text-xl font-black text-white print:text-black mb-2 uppercase italic tracking-tighter">Simulador de Reforma Tributária</h4>
                            <p className="text-end-text-sec text-xs">Projeção baseada no faturamento real dos últimos {simulation.periodo_dias} dias: <span className="text-white font-bold">{simulation.total_faturamento.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}</span></p>
                        </div>
                        <div className="bg-end-success/10 border border-end-success/20 rounded-lg p-3">
                            <p className="text-[10px] font-bold text-end-success uppercase mb-1">Economia em 2028</p>
                            <p className="text-xl font-black text-end-success tracking-tighter">
                                + {simulation.economia_transicao.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
                            </p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                <h4 className="text-sm font-bold text-black uppercase mb-6 tracking-widest">Histórico de Exposição Fiscal (6 Meses)</h4>
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
                    <p className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">Tecnologia Contábil Avançada</p>
                </div>
                <div className="text-[10px] text-gray-400 font-bold uppercase tracking-widest">
                    Gerado em: {new Date().toLocaleString('pt-BR')} • Página 1 de 1
                </div>
            </div>
        </>
    );

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-12 print:p-0 print:space-y-6 relative min-h-[600px]">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 print:hidden">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Relatório de Valor Realizado</h2>
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
                <div className="fixed inset-0 z-[100] bg-end-bg p-12 overflow-y-auto animate-in fade-in zoom-in duration-300 print:hidden">
                    <button
                        onClick={() => setIsPresentationMode(false)}
                        className="absolute top-8 right-8 text-end-text-sec hover:text-white transition-colors"
                    >
                        Esc para sair
                    </button>
                    <div className="max-w-6xl mx-auto">
                        <div className="mb-12 border-b border-end-border pb-8">
                            <h1 className="text-5xl font-black text-white mb-4">Relatório Estratégico de Valor</h1>
                            <p className="text-xl text-end-text-sec">Resultado do monitoramento automatizado para {companies.find(c => c.id === selectedEmpresa)?.razao_social || 'Escritório Consolidado'}</p>
                        </div>
                        <div className="space-y-12">
                            {renderContent()}
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
                        <h3 className="text-3xl font-black text-white italic uppercase tracking-tighter mb-4">Recurso de Alto Valor</h3>
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
                        <h4 className="text-2xl font-black italic tracking-tighter print:text-black">SUA CONTABILIDADE É UM INVESTIMENTO</h4>
                        <p className="font-medium text-black/70 print:text-black/80">Este relatório prova que o monitoramento se paga e gera lucro.</p>
                    </div>
                    <button className="bg-black text-white px-8 py-3 rounded-md font-bold hover:scale-105 transition-transform flex items-center gap-2 print:hidden">
                        Compartilhar com Cliente
                        <ArrowRight size={18} />
                    </button>
                </div>
            )}
        </div>
    );
}
