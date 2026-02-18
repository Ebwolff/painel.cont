import React, { useEffect, useState } from 'react';
import { TrendingUp, ShieldCheck, Download, Calendar, ArrowRight, Wallet, AlertCircle } from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';

export function RelatorioValor() {
    const [roiData, setRoiData] = useState<any>(null);
    const [intelData, setIntelData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

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

            const [roiDataRes, intelDataRes] = await Promise.all([
                api.get(`/roi/summary${suffix}`),
                api.get(`/roi/strategic-intel${suffix}`)
            ]);

            console.log("ROI Res:", roiDataRes);
            console.log("Intel Res:", intelDataRes);

            setRoiData(roiDataRes);
            setIntelData(intelDataRes);
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
                            <div className="bg-white/5 rounded-lg px-4 py-3 border border-white/5 print:bg-gray-50 print:border-gray-200">
                                <p className="text-[10px] text-end-text-sec print:text-gray-500 uppercase mb-1">Créditos de Transição</p>
                                <p className="text-xl font-bold text-white print:text-black">{totalFormatado}</p>
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
        <div className="space-y-8 animate-in fade-in duration-500 pb-12 print:p-0 print:space-y-6">
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

            {/* Action Footer */}
            {!isPresentationMode && (
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
