import React from 'react';
import { cn } from '../lib/utils';

interface RiskThermometerProps {
    score: number; // 0 to 100
    size?: number;
}

export function RiskThermometer({ score, size = 200 }: RiskThermometerProps) {
    // Normalize score
    const safeScore = Math.min(Math.max(score, 0), 100);

    // Color determination
    let statusColor = "text-end-success";
    let statusText = "SEGURO";

    if (safeScore > 30) {
        statusColor = "text-end-warning";
        statusText = "ATENÇÃO";
    }
    if (safeScore > 70) {
        statusColor = "text-end-error";
        statusText = "CRÍTICO";
    }

    // Calculate rotation for needle: -90deg (0) to 90deg (100)
    const rotation = (safeScore / 100) * 180 - 90;

    const radius = size / 2;
    const strokeWidth = 20;
    const innerRadius = radius - strokeWidth;

    return (
        <div className="flex flex-col items-center justify-center">
            <div className="relative" style={{ width: size, height: size / 2 + 20 }}>
                {/* Gauge Background (Semicircle) */}
                <svg width={size} height={size / 2} viewBox={`0 0 ${size} ${size / 2}`} className="overflow-visible">
                    <path
                        d={`M ${strokeWidth / 2} ${radius} A ${innerRadius + strokeWidth / 2} ${innerRadius + strokeWidth / 2} 0 0 1 ${size - strokeWidth / 2} ${radius}`}
                        fill="none"
                        stroke="#333"
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                    />
                    {/* Colored Segments (Could be gradients or segments) */}
                    <path
                        d={`M ${strokeWidth / 2} ${radius} A ${innerRadius + strokeWidth / 2} ${innerRadius + strokeWidth / 2} 0 0 1 ${size / 3} ${radius - size / 3.5}`} // Approx for green segment
                        fill="none"
                        stroke="#10b981" // Green
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                        className="opacity-80"
                    />
                    <path
                        d={`M ${size - strokeWidth / 2} ${radius} A ${innerRadius + strokeWidth / 2} ${innerRadius + strokeWidth / 2} 0 0 0 ${size - size / 3} ${radius - size / 3.5}`} // Approx for red segment
                        fill="none"
                        stroke="#ef4444" // Red
                        strokeWidth={strokeWidth}
                        strokeLinecap="round"
                        className="opacity-80"
                    />
                </svg>

                {/* Needle */}
                <div
                    className="absolute bottom-5 left-1/2 w-1 h-1/2 origin-bottom transition-transform duration-1000 ease-out"
                    style={{
                        transform: `translateX(-50%) rotate(${rotation}deg)`,
                        height: radius - strokeWidth - 10
                    }}
                >
                    <div className="w-full h-full bg-white rounded-t-full shadow-lg relative">
                        <div className="absolute -bottom-2 -left-1.5 w-4 h-4 bg-white rounded-full border-2 border-end-bg"></div>
                    </div>
                </div>
            </div>

            <div className="text-center mt-2">
                <span className={cn("text-3xl font-bold", statusColor)}>{safeScore}%</span>
                <p className="text-xs text-end-text-sec uppercase tracking-widest mt-1">Nível de Risco</p>
                <div className={cn("mt-2 inline-flex px-3 py-1 rounded-full text-xs font-bold bg-white/5 border border-white/10", statusColor)}>
                    {statusText}
                </div>
            </div>
        </div>
    );
}
