import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseKey) {
    // Warn in console but don't crash dev if missing (allows UI work)
    console.warn('Missing Supabase environment variables. Auth and DB features will not work.');
}

export const supabase = createClient(
    supabaseUrl || 'https://placeholder.supabase.co',
    supabaseKey || 'placeholder-key',
    {
        auth: {
            storage: sessionStorage,
            persistSession: true,
            autoRefreshToken: true,
        }
    }
);
