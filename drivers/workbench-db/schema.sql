-- Workbench DB schema v1
-- SQLite для документов, аудита и поиска

PRAGMA foreign_keys = ON;

-- Метаданные схемы
CREATE TABLE IF NOT EXISTS __meta__ (
    key TEXT PRIMARY KEY,
    value TEXT
);

INSERT OR REPLACE INTO __meta__ (key, value) VALUES
    ('schema_version', '1'),
    ('created_at', datetime('now'));

-- Основная таблица документов
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    path TEXT NOT NULL,
    type TEXT CHECK(type IN ('file', 'repo', 'dataset', 'doc')),
    lang TEXT,
    summary TEXT,
    size_bytes INTEGER,
    risk TEXT CHECK(risk IN ('low', 'medium', 'high')),
    source_last_verified TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(source, path)
);

CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
CREATE INDEX IF NOT EXISTS idx_documents_risk ON documents(risk);
CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);

-- Фрагменты документов (для детального поиска)
CREATE TABLE IF NOT EXISTS fragments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    fragment_type TEXT CHECK(fragment_type IN ('heading', 'paragraph', 'code', 'table', 'list', 'quote')),
    content TEXT,
    line_start INTEGER,
    line_end INTEGER,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_fragments_doc ON fragments(document_id);
CREATE INDEX IF NOT EXISTS idx_fragments_type ON fragments(fragment_type);

-- Audit log (append-only)
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT DEFAULT (datetime('now')),
    agent TEXT NOT NULL,
    action TEXT CHECK(action IN ('claim', 'done', 'fail', 'inventory', 'run', 'edit', 'search', 'extract', 'index')),
    target TEXT,
    detail TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_log(ts);
CREATE INDEX IF NOT EXISTS idx_audit_agent ON audit_log(agent);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);

-- Кэш драйверов (статистика)
CREATE TABLE IF NOT EXISTS drivers (
    id TEXT PRIMARY KEY,
    name TEXT,
    level TEXT CHECK(level IN ('L1', 'L2', 'L3')),
    mode TEXT,
    status TEXT CHECK(status IN ('draft', 'ready', 'deprecated')),
    last_run TEXT,
    run_count INTEGER DEFAULT 0
);

-- FTS5 для полнотекстового поиска (опционально, если SQLite поддерживает)
-- Если FTS5 недоступен — fallback на LIKE
