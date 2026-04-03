-- Включение расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Пользовательские типы
CREATE TYPE chat_type AS ENUM ('personal', 'group', 'channel', 'secret');
CREATE TYPE participant_role AS ENUM ('owner', 'admin', 'member');

-- Пользователи
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone_number VARCHAR(20) UNIQUE NOT NULL,
    username VARCHAR(32) UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    status VARCHAR(50) DEFAULT 'online',
    is_bot BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);

-- Сессии
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_name VARCHAR(100),
    device_type VARCHAR(20),
    push_token VARCHAR(255),
    last_active_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ,
    UNIQUE(user_id, device_name)
);

-- Чаты
CREATE TABLE chats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type chat_type NOT NULL,
    title VARCHAR(100),
    avatar_url TEXT,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    last_message_id UUID,
    last_message_at TIMESTAMPTZ,
    last_message_snippet TEXT,
    last_message_sender_id UUID
);

-- Участники чатов
CREATE TABLE chat_participants (
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role participant_role NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_read_message_id UUID,
    notifications_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (chat_id, user_id)
);

-- Сообщения (партиционированные)
CREATE TABLE messages (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id),
    reply_to_message_id UUID,
    text TEXT,
    attachments JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ,
    search_vector tsvector GENERATED ALWAYS AS (to_tsvector('russian', coalesce(text, ''))) STORED,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Файлы
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID,
    file_url TEXT NOT NULL,
    cdn_url TEXT,
    file_type VARCHAR(50),
    mime_type VARCHAR(100),
    file_size BIGINT,
    width INT,
    height INT,
    duration_sec INT,
    preview_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Стикерпаки
CREATE TABLE sticker_packs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(100) NOT NULL,
    author_id UUID REFERENCES users(id) ON DELETE SET NULL,
    is_official BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Стикеры
CREATE TABLE stickers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pack_id UUID NOT NULL REFERENCES sticker_packs(id) ON DELETE CASCADE,
    emoji VARCHAR(10),
    image_url TEXT NOT NULL,
    file_id UUID REFERENCES files(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Контакты
CREATE TABLE user_contacts (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    contact_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    local_name VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, contact_user_id)
);

-- Блокировки
CREATE TABLE user_blocked (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    blocked_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, blocked_user_id)
);

-- Настройки приватности
CREATE TABLE user_privacy_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    last_seen_privacy VARCHAR(20) DEFAULT 'everyone',
    profile_photo_privacy VARCHAR(20) DEFAULT 'everyone',
    bio_privacy VARCHAR(20) DEFAULT 'everyone',
    phone_privacy VARCHAR(20) DEFAULT 'contacts',
    group_invite_privacy VARCHAR(20) DEFAULT 'everyone',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- E2EE сессии
CREATE TABLE e2ee_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    user_a_id UUID NOT NULL REFERENCES users(id),
    user_b_id UUID NOT NULL REFERENCES users(id),
    session_key BYTEA,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (chat_id, user_a_id, user_b_id)
);

-- Prekeys
CREATE TABLE e2ee_prekeys (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    prekey_id INT NOT NULL,
    prekey_data BYTEA NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, prekey_id)
);

-- Боты
CREATE TABLE bots (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    webhook_url TEXT,
    webhook_events TEXT[],
    commands JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Очередь сообщений для ботов
CREATE TABLE bot_message_queue (
    id BIGSERIAL PRIMARY KEY,
    bot_id UUID NOT NULL REFERENCES bots(user_id) ON DELETE CASCADE,
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    retry_count INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at TIMESTAMPTZ
);

-- Аналитика активности (партиционирована)
CREATE TABLE user_activity (
    id BIGSERIAL NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Индексы
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_username ON users(username) WHERE username IS NOT NULL;
CREATE INDEX idx_users_deleted_at ON users(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_sessions_user ON user_sessions(user_id);
CREATE INDEX idx_sessions_revoked ON user_sessions(revoked_at) WHERE revoked_at IS NULL;
CREATE INDEX idx_chats_last_message_at ON chats(last_message_at DESC) WHERE deleted_at IS NULL;
CREATE INDEX idx_chat_participants_user_last_read ON chat_participants(user_id, last_read_message_id) INCLUDE (chat_id, role);
CREATE INDEX idx_messages_chat_id ON messages(chat_id, created_at DESC);
CREATE INDEX idx_messages_sender_id ON messages(sender_id, created_at DESC);
CREATE INDEX idx_messages_search ON messages USING GIN (search_vector);
CREATE INDEX idx_files_message ON files(message_id);
CREATE INDEX idx_stickers_pack ON stickers(pack_id);
CREATE INDEX idx_bots_token_hash ON bots(token_hash);
CREATE INDEX idx_bot_queue_status ON bot_message_queue(status, created_at) WHERE status = 'pending';

-- Триггеры updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chats_updated_at BEFORE UPDATE ON chats FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON messages FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bots_updated_at BEFORE UPDATE ON bots FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Начальные партиции (текущий месяц + 2)
DO $$
DECLARE
    start_date date := date_trunc('month', now())::date;
    i int;
BEGIN
    FOR i IN 0..2 LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS messages_%s PARTITION OF messages
            FOR VALUES FROM (%L) TO (%L)',
            to_char(start_date + (i || ' months')::interval, 'YYYY_MM'),
            start_date + (i || ' months')::interval,
            start_date + ((i+1) || ' months')::interval
        );
    END LOOP;
END;
$$;

DO $$
DECLARE
    start_date date := date_trunc('month', now())::date;
    i int;
BEGIN
    FOR i IN 0..2 LOOP
        EXECUTE format('
            CREATE TABLE IF NOT EXISTS user_activity_%s PARTITION OF user_activity
            FOR VALUES FROM (%L) TO (%L)',
            to_char(start_date + (i || ' months')::interval, 'YYYY_MM'),
            start_date + (i || ' months')::interval,
            start_date + ((i+1) || ' months')::interval
        );
    END LOOP;
END;
$$;

-- Начальные данные
INSERT INTO users (id, phone_number, username, display_name, is_bot)
VALUES (gen_random_uuid(), '+1234567890', 'admin', 'Admin', FALSE)
ON CONFLICT (phone_number) DO NOTHING;