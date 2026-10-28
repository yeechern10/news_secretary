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
    source_id       TEXT UNIQUE,    -- unique identifier for the keyword from the source
    label           TEXT NOT NULL,
    definition      TEXT,
    synonyms        TEXT[],  -- array of synonyms
    keyword_type    TEXT,
    embedding       vector(	1024),  -- for BAAI/bge-m3
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================
-- 3. keyword_relationships
-- =========================================================
CREATE TABLE keyword_relations (
    parent_id UUID REFERENCES keywords(id) ON DELETE CASCADE,
    child_id  UUID REFERENCES keywords(id) ON DELETE CASCADE,
    PRIMARY KEY (parent_id, child_id)
);

-- =========================================================
-- 4. user_keywords
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
-- 5. articles
-- =========================================================
CREATE TABLE IF NOT EXISTS articles (
    id              UUID PRIMARY KEY DEFAULT uuidv7(),
    title           TEXT NOT NULL,
    link            TEXT NOT NULL UNIQUE,
    snippet         TEXT,
    published_at    TIMESTAMPTZ,
    source          TEXT,
    language        TEXT,
    article_type    TEXT,  -- e.g., "news", "discussion", "research"
    content         TEXT,
    content_status  TEXT,  -- e.g., "pending", "completed", "failed"
    content_error   TEXT,  -- error message if content fetching failed
    embedding       vector(1024),            -- for BAAI/bge-m3
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- vector search index for articles embedding
CREATE INDEX IF NOT EXISTS idx_articles_embedding
    ON articles USING hnsw (embedding vector_cosine_ops);

-- TODO: Consider use url hash as unique identifier if using mutiple db

-- =========================================================
-- 6. events
-- =========================================================
CREATE TABLE IF NOT EXISTS events (
    id                          UUID PRIMARY KEY DEFAULT uuidv7(),
    title                       TEXT NOT NULL,
    summary                     TEXT,
    published_at_range_start    TIMESTAMPTZ,
    published_at_range_end      TIMESTAMPTZ,
    confidence_score            REAL,
    importance_score            INTEGER,
    embedding                   vector(1024),  -- for BAAI/bge-m3
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_updated                TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =========================================================
-- 7. user_article_interactions
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
-- 8. user_event_interactions
-- =========================================================
CREATE TABLE IF NOT EXISTS user_event_interactions (
    user_id              UUID NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
    event_id             UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    interaction_type     TEXT NOT NULL,
    interaction_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, event_id)
);

-- =========================================================
-- 9. event_article_relationships
-- =========================================================
CREATE TABLE IF NOT EXISTS event_article_relationships (
    event_id   UUID NOT NULL REFERENCES events(id)   ON DELETE CASCADE,
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, article_id)
);

CREATE INDEX IF NOT EXISTS idx_ear_article ON event_article_relationships(article_id);

-- =========================================================
-- 10. events_keywords_relationships
-- =========================================================
CREATE TABLE IF NOT EXISTS events_keywords_relationships (
    event_id        UUID NOT NULL REFERENCES events(id)   ON DELETE CASCADE,
    keyword_id      UUID   NOT NULL REFERENCES keywords(id) ON DELETE CASCADE,
    relevance_score INTEGER,
    PRIMARY KEY (event_id, keyword_id)
);

CREATE INDEX IF NOT EXISTS idx_ekr_keyword ON events_keywords_relationships(keyword_id);