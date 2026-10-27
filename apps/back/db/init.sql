-- =========================================================
-- Extensions
-- =========================================================
CREATE EXTENSION IF NOT EXISTS vector;          -- pgvector(for vector search)

-- =========================================================
-- 1. users
-- =========================================================
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    username        TEXT NOT NULL UNIQUE,
    country_code    TEXT,
    language        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================
-- 2. keywords
-- =========================================================
CREATE TABLE IF NOT EXISTS keywords (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    keyword         TEXT NOT NULL,
    definition      TEXT,
    synonyms        TEXT,
    parent_id       UUID REFERENCES keywords(id) ON DELETE SET NULL,
    child_ids       TEXT DEFAULT NULL, -- comma-separated list of child keyword IDs
    type            TEXT,
    embedding       vector(	1024),  -- for BAAI/bge-m3
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================
-- 3. user_keywords
--    relationship table between users and keywords, with interest level.
-- =========================================================
CREATE TABLE IF NOT EXISTS user_keywords (
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    keyword_id      UUID   NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    interest_level  INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, keyword_id)
);

-- =========================================================
-- 4. articles
-- =========================================================
CREATE TABLE IF NOT EXISTS articles (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    title           TEXT NOT NULL,
    link            TEXT NOT NULL UNIQUE,
    snippet         TEXT,
    published_at    TIMESTAMPTZ,
    source          TEXT,
    language        TEXT,
    region          TEXT,
    content         TEXT,
    content_status  TEXT,  -- e.g., "success", "failed", "pending"
    content_error   TEXT,  -- error message if content fetching failed
    embedding       vector(1024)            -- for BAAI/bge-m3
);

-- vector search index for articles embedding
CREATE INDEX IF NOT EXISTS idx_articles_embedding
    ON articles USING hnsw (embedding vector_cosine_ops);

-- =========================================================
-- 5. events
-- =========================================================
CREATE TABLE IF NOT EXISTS events (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    event_title                 TEXT NOT NULL,
    event_summary               TEXT,
    published_at_range_start    TIMESTAMPTZ,
    published_at_range_end      TIMESTAMPTZ,
    confidence_score            REAL,
    tags                        TEXT,
    importance_score            INTEGER,
    embedding                   vector(1024),  -- for BAAI/bge-m3
    created_timestamp           TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated_timestamp      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================
-- 6. user_article_interactions
-- =========================================================
CREATE TABLE IF NOT EXISTS user_article_interactions (
    user_id              UUID NOT NULL REFERENCES users(id)    ON DELETE CASCADE,
    article_id           UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    interaction_type     TEXT NOT NULL,
    interaction_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, article_id, interaction_type, interaction_timestamp)
);

CREATE INDEX IF NOT EXISTS idx_uai_user    ON user_article_interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_uai_article ON user_article_interactions(article_id);

-- =========================================================
-- 7. user_event_interactions
-- =========================================================
CREATE TABLE IF NOT EXISTS user_event_interactions (
    user_id              UUID NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    event_id             UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    interaction_type     TEXT NOT NULL,
    interaction_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, event_id)
);

-- =========================================================
-- 8. event_article_relationships
-- =========================================================
CREATE TABLE IF NOT EXISTS event_article_relationships (
    event_id   UUID NOT NULL REFERENCES events(id)   ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, article_id)
);

CREATE INDEX IF NOT EXISTS idx_ear_article ON event_article_relationships(article_id);

-- =========================================================
-- 9. events_keywords_relationships
-- =========================================================
CREATE TABLE IF NOT EXISTS events_keywords_relationships (
    event_id        UUID NOT NULL REFERENCES events(id)   ON DELETE CASCADE,
    keyword_id      UUID   NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    relevance_score INTEGER,
    PRIMARY KEY (event_id, keyword_id)
);

CREATE INDEX IF NOT EXISTS idx_ekr_keyword ON events_keywords_relationships(keyword_id);