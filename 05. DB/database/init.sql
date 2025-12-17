-- init.sql: Crea la estructura de tablas

-- 1. Tablas Catálogos
CREATE TABLE IF NOT EXISTS video_status (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS inspection_status (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    severity INTEGER DEFAULT 0,
    is_anomaly BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS food_category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    min_threshold DOUBLE PRECISION DEFAULT 0.0
);

-- 2. Tablas Operativas
CREATE TABLE IF NOT EXISTS sync_log (
    id SERIAL PRIMARY KEY,
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP,
    found_videos INTEGER DEFAULT 0,
    processed_videos INTEGER DEFAULT 0,
    status VARCHAR(50),
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS video (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    source_url VARCHAR(255),
    date TIMESTAMP,
    
    -- Llaves foráneas
    status_id INTEGER REFERENCES video_status(id),
    log_id INTEGER REFERENCES sync_log(id)
);

CREATE TABLE IF NOT EXISTS inspection (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    video_minute DOUBLE PRECISION,
    percentage DOUBLE PRECISION,
    screenshot_url VARCHAR(255),
    is_false_positive BOOLEAN DEFAULT FALSE,
    model_version VARCHAR(50),
    user_id_validator INTEGER, -- Referencia lógica a Laravel User

    -- Llaves foráneas
    video_id INTEGER REFERENCES video(id),
    category_id INTEGER REFERENCES food_category(id),
    status_id INTEGER REFERENCES inspection_status(id)
);