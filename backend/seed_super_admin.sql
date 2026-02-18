-- EXECUTE ESSE SCRIPT NO SUPABASE (SQL EDITOR)

-- 1. Substitua 'seu@email.com' pelo email real que você está usando no login
-- O script vai procurar o usuário pelo email e atualizar a role para 'super_admin'

DO $$
DECLARE
    target_email TEXT := 'seu@email.com'; -- <--- COLOQUE SEU EMAIL AQUI
    target_user_id UUID;
BEGIN
    -- Buscar ID do usuário
    SELECT id INTO target_user_id FROM auth.users WHERE email = target_email;

    IF target_user_id IS NOT NULL THEN
        -- Atualizar Profile
        UPDATE public.profiles
        SET role = 'super_admin'
        WHERE id = target_user_id;

        -- Garantir permissões iniciais no JSONB (opcional, mas bom ter)
        UPDATE public.profiles
        SET permissions = '{
            "can_manage_tenants": true,
            "can_manage_users": true,
            "can_view_metrics": true
        }'::jsonb
        WHERE id = target_user_id;
        
        RAISE NOTICE 'Usuário % promovido a SUPER ADMIN com sucesso!', target_email;
    ELSE
        RAISE NOTICE 'Usuário % não encontrado. Faça login/cadastro primeiro.', target_email;
    END IF;
END $$;
