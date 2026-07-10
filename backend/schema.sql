CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    qq VARCHAR(20),
    email VARCHAR(100),
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
    lost_time TIMESTAMP,
    found_time TIMESTAMP,
    status VARCHAR(20) DEFAULT 'lost',
    image_url VARCHAR(500),
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_qq VARCHAR(20),
    user_id INTEGER REFERENCES users(id),
    vector VECTOR(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS match_records (
    id SERIAL PRIMARY KEY,
    lost_item_id INTEGER REFERENCES lost_items(id),
    match_item_id INTEGER REFERENCES lost_items(id),
    similarity FLOAT,
    match_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- pgvector 0.8.x 索引维度上限 2000，Qwen3-VL 实际输出为 1536，如果数据量大可以考虑放开以下索引注释：
-- CREATE INDEX idx_lost_items_vector ON lost_items USING hnsw (vector vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_lost_items_status ON lost_items(status);
CREATE INDEX IF NOT EXISTS idx_lost_items_type ON lost_items(item_type);
CREATE INDEX IF NOT EXISTS idx_lost_items_user_id ON lost_items(user_id);
