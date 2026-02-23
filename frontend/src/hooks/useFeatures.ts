import { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../services/api';

// Todas as features são liberadas para todos os planos.
// A diferenciação é apenas no limite de empresas (volume).
const ALL_FEATURES = [
    'basic_monitor', 'upload_manual', 'roi_summary',
    'advanced_alerts', 'sefaz_sync', 'tax_reform_simulator',
    'ai_anomaly_detection', 'executive_reports'
];

export interface FeatureLayout {
    tier: 'starter' | 'pro' | 'enterprise';
    features: string[];
    usage?: {
        companies_limit: number;
        companies_count: number;
    };
}

export function useFeatures() {
    const [featureData, setFeatureData] = useState<FeatureLayout | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;
        async function loadFeatures() {
            try {
                const data = await api.get('/features/my-features');
                if (isMounted) setFeatureData(data);
            } catch (error) {
                console.error("Failed to load features", error);
                // Fallback: todas as features liberadas
                if (isMounted) setFeatureData({ tier: 'starter', features: ALL_FEATURES });
            } finally {
                if (isMounted) setLoading(false);
            }
        }
        loadFeatures();
        return () => { isMounted = false; };
    }, []);

    // hasFeature agora sempre retorna true (todas liberadas)
    const hasFeature = useCallback((_featureName: string) => {
        return true;
    }, []);

    const isTier = useCallback((tierName: string) => {
        return featureData?.tier === tierName;
    }, [featureData]);

    const memoizedFeatures = useMemo(() => featureData?.features || ALL_FEATURES, [featureData]);

    return {
        tier: featureData?.tier || 'starter',
        features: memoizedFeatures,
        hasFeature,
        isTier,
        loading,
        usage: featureData?.usage
    };
}
