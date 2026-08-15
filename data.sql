-- ============================================
-- COMPLETE DATABASE SCHEMA - FINAL VERSION
-- ✅ All tables for WhatsApp + Client Stats
-- ✅ No unique constraints on users
-- ✅ MongoDB replacement ready
-- ============================================

-- STEP 1: DROP EXISTING FUNCTIONS
DROP FUNCTION IF EXISTS get_user_generation_history(UUID) CASCADE;
DROP FUNCTION IF EXISTS get_pending_notifications() CASCADE;
DROP FUNCTION IF EXISTS link_session_to_user(TEXT, UUID) CASCADE;

-- STEP 2: DROP OLD VERIFICATION TABLES
DROP TABLE IF EXISTS phone_otp_logs CASCADE;
DROP TABLE IF EXISTS email_logs CASCADE;
DROP VIEW IF EXISTS user_stats CASCADE;
DROP VIEW IF EXISTS notification_dashboard CASCADE;

-- STEP 3: DROP ALL UNIQUE CONSTRAINTS FROM USERS TABLE
ALTER TABLE IF EXISTS users DROP CONSTRAINT IF EXISTS users_email_key;
ALTER TABLE IF EXISTS users DROP CONSTRAINT IF EXISTS users_phone_number_key;
ALTER TABLE IF EXISTS users DROP CONSTRAINT IF EXISTS users_pkey CASCADE;

-- STEP 4: DROP AND RECREATE ALL TABLES
DROP TABLE IF EXISTS client_stats CASCADE;
DROP TABLE IF EXISTS welcome_email_logs CASCADE;
DROP TABLE IF EXISTS user_generations CASCADE;
DROP TABLE IF EXISTS scheduled_notifications CASCADE;
DROP TABLE IF EXISTS generation_logs CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- ============================================
-- TABLE CREATION
-- ============================================

-- TABLE 1: USERS (with WhatsApp tracking)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    country_code TEXT DEFAULT 'IN',
    pre_registration_generations INTEGER DEFAULT 0,
    total_generations INTEGER DEFAULT 0,
    
    -- WhatsApp notification tracking
    whatsapp_notification_sent BOOLEAN DEFAULT FALSE,
    notification_sent_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_generation_at TIMESTAMPTZ,
    ip_address TEXT,
    user_agent TEXT
);

-- TABLE 2: SESSIONS
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL UNIQUE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    generation_count INTEGER DEFAULT 0,
    is_registered BOOLEAN DEFAULT FALSE,
    status VARCHAR(50) DEFAULT 'active',
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- TABLE 3: GENERATION LOGS
CREATE TABLE generation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT NOT NULL,
    client_name TEXT NOT NULL DEFAULT 'skyline',
    room_type TEXT NOT NULL,
    style TEXT,
    custom_prompt TEXT,
    cloudinary_url TEXT,
    generation_number INTEGER NOT NULL,
    was_registered BOOLEAN DEFAULT FALSE,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABLE 4: SCHEDULED NOTIFICATIONS (WhatsApp/SMS)
CREATE TABLE scheduled_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    phone_number TEXT NOT NULL,
    country_code TEXT NOT NULL DEFAULT 'IN',
    scheduled_for TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    delivery_method VARCHAR(20),
    sent_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABLE 5: USER GENERATIONS (with download tracking)
CREATE TABLE user_generations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id TEXT,
    generation_id TEXT,
    client_name TEXT NOT NULL,
    room_type TEXT NOT NULL,
    style TEXT,
    custom_prompt TEXT,
    image_url TEXT,
    
    -- Download tracking
    downloaded BOOLEAN DEFAULT FALSE,
    download_count INTEGER DEFAULT 0,
    downloaded_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- TABLE 6: WELCOME EMAIL LOGS
CREATE TABLE welcome_email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    sent_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'sent',
    error_message TEXT
);

-- TABLE 7: CLIENT STATS (replaces MongoDB)
CREATE TABLE client_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_name TEXT UNIQUE NOT NULL,
    total_generations INTEGER DEFAULT 0,
    total_downloads INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Users indexes
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created ON users(created_at DESC);
CREATE INDEX idx_users_whatsapp_sent ON users(whatsapp_notification_sent);

-- Sessions indexes
CREATE INDEX idx_sessions_session_id ON sessions(session_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_status ON sessions(status);

-- Generation logs indexes
CREATE INDEX idx_generation_logs_user ON generation_logs(user_id);
CREATE INDEX idx_generation_logs_session ON generation_logs(session_id);
CREATE INDEX idx_generation_logs_created ON generation_logs(created_at DESC);
CREATE INDEX idx_generation_logs_client ON generation_logs(client_name);

-- Scheduled notifications indexes
CREATE INDEX idx_scheduled_notifications_status ON scheduled_notifications(status);
CREATE INDEX idx_scheduled_notifications_scheduled_for ON scheduled_notifications(scheduled_for);
CREATE INDEX idx_scheduled_notifications_user ON scheduled_notifications(user_id);

-- User generations indexes
CREATE INDEX idx_user_generations_user ON user_generations(user_id);
CREATE INDEX idx_user_generations_session ON user_generations(session_id);
CREATE INDEX idx_user_generations_created ON user_generations(created_at DESC);
CREATE INDEX idx_user_generations_client ON user_generations(client_name);

-- Welcome email logs indexes
CREATE INDEX idx_welcome_email_logs_user ON welcome_email_logs(user_id);

-- Client stats indexes
CREATE INDEX idx_client_stats_name ON client_stats(client_name);

-- ============================================
-- INSERT DEFAULT DATA
-- ============================================

-- Insert default clients
INSERT INTO client_stats (client_name, total_generations, total_downloads)
VALUES 
  ('skyline', 0, 0),
  ('ellington', 0, 0)
ON CONFLICT (client_name) DO NOTHING;

-- ============================================
-- HELPER FUNCTIONS
-- ============================================

-- Function 1: Get user generation history
CREATE OR REPLACE FUNCTION get_user_generation_history(user_uuid UUID)
RETURNS TABLE (
    generation_id UUID,
    room_type TEXT,
    style TEXT,
    custom_prompt TEXT,
    image_url TEXT,
    generated_at TIMESTAMPTZ,
    downloaded BOOLEAN,
    download_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ug.id,
        ug.room_type,
        ug.style,
        ug.custom_prompt,
        ug.image_url,
        ug.created_at,
        ug.downloaded,
        ug.download_count
    FROM user_generations ug
    WHERE ug.user_id = user_uuid
    ORDER BY ug.created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function 2: Get pending notifications
CREATE OR REPLACE FUNCTION get_pending_notifications()
RETURNS TABLE (
    notification_id UUID,
    user_id UUID,
    user_name TEXT,
    phone_number TEXT,
    country_code TEXT,
    scheduled_for TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        sn.id,
        sn.user_id,
        u.full_name,
        sn.phone_number,
        sn.country_code,
        sn.scheduled_for
    FROM scheduled_notifications sn
    JOIN users u ON u.id = sn.user_id
    WHERE sn.status = 'pending'
      AND sn.scheduled_for <= NOW()
    ORDER BY sn.scheduled_for ASC;
END;
$$ LANGUAGE plpgsql;

-- Function 3: Link session to user
CREATE OR REPLACE FUNCTION link_session_to_user(
    p_session_id TEXT,
    p_user_id UUID
)
RETURNS INTEGER AS $$
DECLARE
    linked_count INTEGER;
BEGIN
    UPDATE user_generations
    SET user_id = p_user_id
    WHERE session_id = p_session_id
      AND user_id IS NULL;
    
    GET DIAGNOSTICS linked_count = ROW_COUNT;
    
    RETURN linked_count;
END;
$$ LANGUAGE plpgsql;

-- Function 4: Track image download
CREATE OR REPLACE FUNCTION track_image_download(
    p_generation_id TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    current_count INTEGER;
BEGIN
    -- Get current download count
    SELECT download_count INTO current_count
    FROM user_generations
    WHERE generation_id = p_generation_id;
    
    -- Update download tracking
    UPDATE user_generations
    SET 
        downloaded = TRUE,
        download_count = COALESCE(current_count, 0) + 1,
        downloaded_at = NOW()
    WHERE generation_id = p_generation_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- VIEWS FOR ANALYTICS
-- ============================================

-- View 1: User Statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.full_name,
    u.email,
    u.phone_number,
    u.country_code,
    u.pre_registration_generations,
    u.total_generations,
    u.created_at as registered_at,
    u.last_generation_at,
    u.whatsapp_notification_sent,
    u.notification_sent_at,
    COUNT(DISTINCT gl.id) as generation_count,
    COUNT(DISTINCT ug.id) as total_images_generated,
    MAX(gl.created_at) as last_generated,
    COALESCE(wel.status, 'not_sent') as welcome_email_status,
    COALESCE(sn.status, 'not_scheduled') as whatsapp_status,
    sn.delivery_method as notification_method
FROM users u
LEFT JOIN generation_logs gl ON u.id = gl.user_id
LEFT JOIN user_generations ug ON u.id = ug.user_id
LEFT JOIN welcome_email_logs wel ON u.id = wel.user_id
LEFT JOIN scheduled_notifications sn ON u.id = sn.user_id
GROUP BY u.id, wel.status, sn.status, sn.delivery_method;

-- View 2: Notification Dashboard
CREATE OR REPLACE VIEW notification_dashboard AS
SELECT 
    DATE(sn.created_at) as date,
    COUNT(*) as total_scheduled,
    COUNT(*) FILTER (WHERE sn.status = 'sent') as sent_count,
    COUNT(*) FILTER (WHERE sn.status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE sn.status = 'pending') as pending_count,
    COUNT(*) FILTER (WHERE sn.delivery_method = 'whatsapp') as whatsapp_count,
    COUNT(*) FILTER (WHERE sn.delivery_method = 'sms') as sms_count
FROM scheduled_notifications sn
GROUP BY DATE(sn.created_at)
ORDER BY date DESC;

-- View 3: Client Statistics
CREATE OR REPLACE VIEW client_dashboard AS
SELECT 
    cs.client_name,
    cs.total_generations,
    cs.total_downloads,
    COUNT(DISTINCT ug.user_id) as unique_users,
    COUNT(DISTINCT ug.id) as total_images,
    MAX(ug.created_at) as last_generation,
    cs.created_at as client_added_at,
    cs.updated_at as last_updated
FROM client_stats cs
LEFT JOIN user_generations ug ON cs.client_name = ug.client_name
GROUP BY cs.client_name, cs.total_generations, cs.total_downloads, cs.created_at, cs.updated_at;

-- ============================================
-- COMMENTS (Documentation)
-- ============================================

COMMENT ON TABLE users IS 'Stores all user registrations - NO UNIQUE CONSTRAINTS - Duplicates allowed for testing';
COMMENT ON TABLE scheduled_notifications IS 'Stores scheduled WhatsApp/SMS notifications sent 30 minutes after registration';
COMMENT ON TABLE user_generations IS 'Links all generated images to users with download tracking';
COMMENT ON TABLE client_stats IS 'Tracks statistics per client (replaces MongoDB clients collection)';
COMMENT ON TABLE generation_logs IS 'Detailed logs of all generation requests';
COMMENT ON TABLE sessions IS 'Tracks anonymous and registered user sessions';
COMMENT ON TABLE welcome_email_logs IS 'Logs all welcome emails sent to users';

COMMENT ON FUNCTION get_user_generation_history IS 'Get complete generation history for a specific user';
COMMENT ON FUNCTION get_pending_notifications IS 'Get all notifications that are due to be sent now';
COMMENT ON FUNCTION link_session_to_user IS 'Link pre-registration generations to user account';
COMMENT ON FUNCTION track_image_download IS 'Track when a user downloads a generated image';

-- ============================================
-- VERIFICATION & TESTING
-- ============================================

-- Check 1: Verify all tables exist
SELECT 
    '✅ TABLES CREATED' as check_type,
    COUNT(*) as table_count,
    STRING_AGG(table_name, ', ' ORDER BY table_name) as tables
FROM information_schema.tables
WHERE table_name IN (
    'users', 
    'sessions',
    'generation_logs',
    'scheduled_notifications', 
    'user_generations', 
    'welcome_email_logs',
    'client_stats'
)
AND table_schema = 'public';

-- Check 2: Verify no unique constraints on users
SELECT 
    '✅ NO UNIQUE CONSTRAINTS' as check_type,
    COUNT(*) as unique_constraint_count
FROM information_schema.table_constraints 
WHERE table_name = 'users' 
  AND constraint_type = 'UNIQUE';

-- Check 3: Verify WhatsApp columns exist
SELECT 
    '✅ WHATSAPP COLUMNS' as check_type,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'users' 
  AND column_name IN ('whatsapp_notification_sent', 'notification_sent_at')
ORDER BY column_name;

-- Check 4: Verify download tracking columns
SELECT 
    '✅ DOWNLOAD TRACKING' as check_type,
    column_name,
    data_type,
    column_default
FROM information_schema.columns 
WHERE table_name = 'user_generations' 
  AND column_name IN ('downloaded', 'download_count', 'downloaded_at')
ORDER BY column_name;

-- Check 5: Verify client stats data
SELECT 
    '✅ CLIENT STATS' as check_type,
    client_name,
    total_generations,
    total_downloads
FROM client_stats
ORDER BY client_name;

-- Check 6: Verify indexes
SELECT 
    '✅ INDEXES CREATED' as check_type,
    COUNT(*) as index_count
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN (
      'users', 'sessions', 'generation_logs', 
      'scheduled_notifications', 'user_generations', 
      'welcome_email_logs', 'client_stats'
  );

-- Check 7: Verify functions
SELECT 
    '✅ FUNCTIONS CREATED' as check_type,
    COUNT(*) as function_count
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
  AND p.proname IN (
      'get_user_generation_history',
      'get_pending_notifications',
      'link_session_to_user',
      'track_image_download'
  );

-- Check 8: Verify views
SELECT 
    '✅ VIEWS CREATED' as check_type,
    COUNT(*) as view_count
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN ('user_stats', 'notification_dashboard', 'client_dashboard');

-- ============================================
-- FINAL SUCCESS MESSAGE
-- ============================================

SELECT 
    '🎉 SETUP COMPLETE!' as status,
    '7 tables, 4 functions, 3 views' as created,
    (SELECT COUNT(*) FROM client_stats) as clients_ready,
    'MongoDB replacement ready' as migration_status,
    'WhatsApp scheduler ready' as notification_status;