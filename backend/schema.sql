DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension unavailable: %, vector search disabled', SQLERRM;
END $$;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    qq VARCHAR(20),
    email VARCHAR(100),
    school_email VARCHAR(320),
    contact_email VARCHAR(320),
    school_email_verified_at TIMESTAMP,
    casdoor_sub VARCHAR(200) UNIQUE,
    casdoor_name VARCHAR(200),
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lost_items (
    id SERIAL PRIMARY KEY,
    item_name VARCHAR(200) NOT NULL,
    item_type VARCHAR(50),
    description TEXT,
    location VARCHAR(200),
    storage_location VARCHAR(200),
    lost_time TIMESTAMP,
    found_time TIMESTAMP,
    direction VARCHAR(20) NOT NULL DEFAULT 'lost',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    contact_visibility VARCHAR(20) NOT NULL DEFAULT 'private',
    image_url VARCHAR(500),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_qq VARCHAR(20),
    contact_email VARCHAR(100),
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT lost_items_direction_check CHECK (direction IN ('lost', 'found')),
    CONSTRAINT lost_items_status_check CHECK (status IN ('active', 'recovered', 'expired')),
    CONSTRAINT lost_items_contact_visibility_check CHECK (contact_visibility IN ('private', 'logged_in', 'claimed', 'public'))
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    message TEXT,
    notification_type VARCHAR(50) DEFAULT 'system',
    related_item_id INTEGER REFERENCES lost_items(id) ON DELETE SET NULL,
    link_url VARCHAR(500),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS claim_requests (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES lost_items(id) ON DELETE CASCADE,
    requester_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    owner_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    request_type VARCHAR(20) NOT NULL DEFAULT 'claim',
    requester_name VARCHAR(100) NOT NULL,
    requester_contact VARCHAR(200) NOT NULL,
    requester_school_email VARCHAR(320),
    message TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'submitted',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT claim_requests_type_check CHECK (request_type IN ('claim', 'contact')),
    CONSTRAINT claim_requests_status_check CHECK (status IN ('submitted', 'completed', 'rejected')),
    CONSTRAINT claim_requests_unique_user_item_type UNIQUE (item_id, requester_user_id, request_type)
);

CREATE TABLE IF NOT EXISTS match_records (
    id SERIAL PRIMARY KEY,
    lost_item_id INTEGER REFERENCES lost_items(id),
    match_item_id INTEGER REFERENCES lost_items(id),
    similarity FLOAT,
    match_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_knowledge_sources (
    id SERIAL PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_knowledge_chunks (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES support_knowledge_sources(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    embedding JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS support_chat_sessions (
    id UUID PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    anonymous_key TEXT,
    channel VARCHAR(20) NOT NULL DEFAULT 'web',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_chat_messages (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES support_chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT support_chat_messages_role_check CHECK (role IN ('user', 'assistant'))
);

-- 兼容已存在的旧表：CREATE TABLE IF NOT EXISTS 不会为旧表补新增列。
ALTER TABLE users ADD COLUMN IF NOT EXISTS school_email VARCHAR(320);
ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_email VARCHAR(320);
ALTER TABLE users ADD COLUMN IF NOT EXISTS school_email_verified_at TIMESTAMP;
ALTER TABLE claim_requests ADD COLUMN IF NOT EXISTS requester_school_email VARCHAR(320);
ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS storage_location VARCHAR(200);
ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS found_time TIMESTAMP;
ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS direction VARCHAR(20) NOT NULL DEFAULT 'lost';
ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'active';
ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS contact_visibility VARCHAR(20) NOT NULL DEFAULT 'private';
ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS contact_email VARCHAR(100);
ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 旧 email 无法证明完成过学校邮箱验证，只迁移为可修改的联系邮箱。
-- school_email 会在用户下次通过 Casdoor 登录时绑定并记录真实验证时间。
UPDATE users
SET contact_email = email
WHERE contact_email IS NULL AND email IS NOT NULL;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'vector') THEN
        EXECUTE 'ALTER TABLE lost_items ADD COLUMN IF NOT EXISTS vector VECTOR(1536)';
    END IF;
END $$;

-- 同步旧数据迁移后的 SERIAL sequence，避免从 MAX(id)+1 切回自增时发生主键冲突。
SELECT setval(pg_get_serial_sequence('users', 'id'), (SELECT COALESCE(MAX(id), 0) + 1 FROM users), false);
SELECT setval(pg_get_serial_sequence('lost_items', 'id'), (SELECT COALESCE(MAX(id), 0) + 1 FROM lost_items), false);
SELECT setval(pg_get_serial_sequence('notifications', 'id'), (SELECT COALESCE(MAX(id), 0) + 1 FROM notifications), false);
SELECT setval(pg_get_serial_sequence('claim_requests', 'id'), (SELECT COALESCE(MAX(id), 0) + 1 FROM claim_requests), false);
SELECT setval(pg_get_serial_sequence('match_records', 'id'), (SELECT COALESCE(MAX(id), 0) + 1 FROM match_records), false);
SELECT setval(pg_get_serial_sequence('support_knowledge_sources', 'id'), (SELECT COALESCE(MAX(id), 0) + 1 FROM support_knowledge_sources), false);
SELECT setval(pg_get_serial_sequence('support_knowledge_chunks', 'id'), (SELECT COALESCE(MAX(id), 0) + 1 FROM support_knowledge_chunks), false);
SELECT setval(pg_get_serial_sequence('support_chat_messages', 'id'), (SELECT COALESCE(MAX(id), 0) + 1 FROM support_chat_messages), false);

-- 开启 HNSW 高维向量索引，加速匹配效率（1536 维 < pgvector HNSW 上限 2000）。
-- 本地只跑 BM25 时可以不安装 pgvector，向量列和索引会跳过。
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'lost_items' AND column_name = 'vector'
    ) THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_lost_items_vector ON lost_items USING hnsw (vector vector_cosine_ops)';
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_lost_items_status ON lost_items(status);
CREATE INDEX IF NOT EXISTS idx_lost_items_direction ON lost_items(direction);
CREATE INDEX IF NOT EXISTS idx_lost_items_type ON lost_items(item_type);
CREATE INDEX IF NOT EXISTS idx_lost_items_user_id ON lost_items(user_id);
CREATE INDEX IF NOT EXISTS idx_lost_items_contact_visibility ON lost_items(contact_visibility);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_school_email_unique ON users(LOWER(school_email)) WHERE school_email IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_claim_requests_item_id ON claim_requests(item_id);
CREATE INDEX IF NOT EXISTS idx_claim_requests_requester ON claim_requests(requester_user_id);
CREATE INDEX IF NOT EXISTS idx_claim_requests_school_email ON claim_requests(requester_school_email);
CREATE INDEX IF NOT EXISTS idx_claim_requests_owner ON claim_requests(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_claim_requests_created_at ON claim_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_support_knowledge_chunks_source_id ON support_knowledge_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_support_chat_sessions_user_id ON support_chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_support_chat_sessions_anonymous_key ON support_chat_sessions(anonymous_key);
CREATE INDEX IF NOT EXISTS idx_support_chat_messages_session_id ON support_chat_messages(session_id);
