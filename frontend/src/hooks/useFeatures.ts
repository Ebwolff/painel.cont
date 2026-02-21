import { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../services/api';

export interface FeatureLayout {
    tier: 'starter' | 'pro' | 'enterprise';
    features: string[];
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
                // Fallback to starter
                if (isMounted) setFeatureData({ tier: 'starter', features: ['basic_monitor', 'upload_manual'] });
            } finally {
                if (isMounted) setLoading(false);
            }
        }
        loadFeatures();
        return () => { isMounted = false; };
    }, []);

    const hasFeature = useCallback((featureName: string) => {
        return featureData?.features.includes(featureName) || false;
    }, [featureData]);

    const isTier = useCallback((tierName: string) => {
        return featureData?.tier === tierName;
    }, [featureData]);

    const memoizedFeatures = useMemo(() => featureData?.features || [], [featureData]);

    return {
        tier: featureData?.tier || 'starter',
        features: memoizedFeatures,
        hasFeature,
        isTier,
        loading
    };
}
