import { supabase } from '../lib/supabase';

const API_URL = '/api';

async function getHeaders() {
    const { data } = await supabase.auth.getSession();
    const headers: Record<string, string> = {
        'Content-Type': 'application/json',
    };

    if (data.session?.access_token) {
        headers['Authorization'] = `Bearer ${data.session.access_token}`;
    }

    return headers;
}

async function handleResponse(response: Response) {
    if (response.status === 401) {
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
}

export const api = {
    get: async (endpoint: string) => {
        const headers = await getHeaders();
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'GET',
            headers,
        });
        return handleResponse(response);
    },

    post: async (endpoint: string, body: any) => {
        const headers = await getHeaders();
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers,
            body: JSON.stringify(body),
        });
        return handleResponse(response);
    },

    put: async (endpoint: string, body: any) => {
        const headers = await getHeaders();
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'PUT',
            headers,
            body: JSON.stringify(body),
        });
        return handleResponse(response);
    },

    delete: async (endpoint: string) => {
        const headers = await getHeaders();
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'DELETE',
            headers,
        });
        return handleResponse(response);
    },

    // Helper para upload de arquivos (FormData)
    upload: async (endpoint: string, formData: FormData) => {
        const { data } = await supabase.auth.getSession();
        const headers: Record<string, string> = {}; // Content-Type for FormData is automatic

        if (data.session?.access_token) {
            headers['Authorization'] = `Bearer ${data.session.access_token}`;
        }

        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers,
            body: formData,
        });

        if (response.status === 401) {
            window.location.href = '/login';
            throw new Error('Unauthorized');
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || 'Upload Error');
        }

        return response.json();
    }
};
