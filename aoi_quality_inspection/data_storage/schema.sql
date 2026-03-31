-- 产品型号表
CREATE TABLE IF NOT EXISTS product_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    feature_lib_path TEXT,
    threshold REAL DEFAULT 0.5,
    is_active BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 样本表
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_model_id INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    aoi_result INTEGER,
    ai_score REAL,
    ai_label INTEGER,
    confidence REAL,
    is_uncertain BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_model_id) REFERENCES product_models(id)
);

-- 标注表
CREATE TABLE IF NOT EXISTS annotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id INTEGER NOT NULL,
    label INTEGER NOT NULL,
    defect_type TEXT,
    operator TEXT NOT NULL,
    annotated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    FOREIGN KEY (sample_id) REFERENCES samples(id)
);

-- 模型版本表
CREATE TABLE IF NOT EXISTS model_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_model_id INTEGER NOT NULL,
    version TEXT NOT NULL,
    feature_lib_path TEXT NOT NULL,
    num_samples INTEGER DEFAULT 0,
    accuracy REAL,
    is_active BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_model_id) REFERENCES product_models(id)
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'operator',
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 性能指标表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_model_id INTEGER,
    metric_type TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY (product_model_id) REFERENCES product_models(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_samples_product_model ON samples(product_model_id);
CREATE INDEX IF NOT EXISTS idx_samples_timestamp ON samples(timestamp);
CREATE INDEX IF NOT EXISTS idx_samples_ai_label ON samples(ai_label);
CREATE INDEX IF NOT EXISTS idx_samples_is_uncertain ON samples(is_uncertain);
CREATE INDEX IF NOT EXISTS idx_annotations_sample ON annotations(sample_id);
CREATE INDEX IF NOT EXISTS idx_annotations_operator ON annotations(operator);
CREATE INDEX IF NOT EXISTS idx_model_versions_product ON model_versions(product_model_id);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
