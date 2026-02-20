import { useState, useEffect } from 'react';
import { api } from '../services/api';

export interface FeatureLayout {
    tier: 'starter' | 'pro' | 'enterprise';
    features: string[];
}

export function useFeatures() {
    const [featureData, setFeatureData] = useState<FeatureLayout | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function loadFeatures() {
            try {
                const data = await api.get('/features/my-features');
                setFeatureData(data);
            } catch (error) {
                console.error("Failed to load features", error);
                // Fallback to starter
                setFeatureData({ tier: 'starter', features: ['basic_monitor', 'upload_manual'] });
            } finally {
                setLoading(false);
            }
        }
        loadFeatures();
    }, []);

    const hasFeature = (featureName: string) => {
        return featureData?.features.includes(featureName) || false;
    };

    const isTier = (tierName: string) => {
        return featureData?.tier === tierName;
    };

    return {
        tier: featureData?.tier || 'starter',
        features: featureData?.features || [],
        hasFeature,
        isTier,
        loading
    };
}
