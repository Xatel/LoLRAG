-- League of Legends Wiki Database Schema
CREATE EXTENSION IF NOT EXISTS vector;
-- TODO: Consider adding other tables for items, runes, summoner spells, etc. in the future as the project expands.

-- ============================================================================
-- CONTENT PAGES (for source tracking)
-- ============================================================================

CREATE TABLE content_pages (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) UNIQUE NOT NULL,
    title VARCHAR(200) NOT NULL,
    last_scraped TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CHAMPION TABLES
-- ============================================================================

CREATE TABLE champions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    title VARCHAR(200),
    bio TEXT,
    role VARCHAR(50),
    resource_type VARCHAR(50), -- 'Mana', 'Energy', 'Fury', 'None', etc.
    range_type VARCHAR(20), -- 'Melee', 'Ranged'
    release_date DATE,
    content_page_id INTEGER REFERENCES content_pages(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE abilities (
    id SERIAL PRIMARY KEY,
    champion_id INTEGER NOT NULL REFERENCES champions(id) ON DELETE CASCADE,
    ability_name VARCHAR(100) NOT NULL,
    ability_key VARCHAR(1), -- 'P', 'Q', 'W', 'E', 'R'
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ability stats per level
CREATE TABLE ability_levels (
    id SERIAL PRIMARY KEY,
    ability_id INTEGER NOT NULL REFERENCES abilities(id) ON DELETE CASCADE,
    level INTEGER CHECK (level >= 1 AND level <= 5),
    cooldown VARCHAR(100),
    cost VARCHAR(100),
    range VARCHAR(100),
    damage_ratio VARCHAR(100), -- e.g., "0.5 AD" or "0.8 AP"
    additional_info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ability_id, level)
);

-- Champion stats at level 1
-- Champions at X level can be calculated using the base stat + (stat_per_level * (X - 1))
CREATE TABLE champion_stats (
    id SERIAL PRIMARY KEY,
    champion_id INTEGER UNIQUE NOT NULL REFERENCES champions(id) ON DELETE CASCADE,
    hp FLOAT,
    hp_per_level FLOAT,
    mana FLOAT,
    mana_per_level FLOAT,
    armor FLOAT,
    armor_per_level FLOAT,
    magic_resist FLOAT,
    magic_resist_per_level FLOAT,
    attack_damage FLOAT,
    attack_damage_per_level FLOAT,
    attack_speed FLOAT,
    attack_speed_per_level FLOAT,
    movement_speed FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONTENT CHUNKS (for RAG)
-- ============================================================================

CREATE TABLE content_chunks (
    id SERIAL PRIMARY KEY,
    champion_id INTEGER NOT NULL REFERENCES champions(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    section_title VARCHAR(200),
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SEARCH ANALYTICS
-- ============================================================================

CREATE TABLE search_history (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    query_embedding vector(1536),
    result_count INTEGER,
    session_id VARCHAR(100),
    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Vector similarity indexes
CREATE INDEX ON content_chunks USING IVFFLAT (embedding vector_cosine_ops);
CREATE INDEX ON search_history USING IVFFLAT (query_embedding vector_cosine_ops);

-- Text search indexes
CREATE INDEX ON abilities USING GIN (to_tsvector('english', description));
CREATE INDEX ON champions USING GIN (to_tsvector('english', bio));
CREATE INDEX ON content_chunks USING GIN (to_tsvector('english', chunk_text));

-- Lookup indexes
CREATE INDEX ON champions(name);
CREATE INDEX ON champions(role);
CREATE INDEX ON abilities(champion_id);
CREATE INDEX ON ability_levels(ability_id);
CREATE INDEX ON content_chunks(champion_id);

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Champion with full details and abilities with per-level stats
CREATE VIEW champion_full_view AS
SELECT 
    c.id,
    c.name,
    c.title,
    c.role,
    c.resource_type,
    c.range_type,
    c.bio,
    cs.hp,
    cs.mana,
    cs.attack_damage,
    cs.ability_power,
    cs.armor,
    cs.magic_resist,
    cs.attack_speed,
    cs.movement_speed,
    json_agg(
        json_build_object(
            'ability_key', a.ability_key,
            'name', a.ability_name,
            'description', a.description,
            'levels', (
                SELECT json_agg(
                    json_build_object(
                        'level', al.level,
                        'cooldown', al.cooldown,
                        'cost', al.cost,
                        'range', al.range,
                        'damage_ratio', al.damage_ratio,
                        'additional_info', al.additional_info
                    ) ORDER BY al.level
                )
                FROM ability_levels al
                WHERE al.ability_id = a.id
            )
        ) ORDER BY 
            CASE a.ability_key
                WHEN 'P' THEN 0
                WHEN 'Q' THEN 1
                WHEN 'W' THEN 2
                WHEN 'E' THEN 3
                WHEN 'R' THEN 4
            END
    ) FILTER (WHERE a.id IS NOT NULL) AS abilities
FROM champions c
LEFT JOIN abilities a ON c.id = a.champion_id
LEFT JOIN champion_stats cs ON c.id = cs.champion_id
GROUP BY c.id, c.name, c.title, c.role, c.resource_type, c.range_type, c.bio,
         cs.hp, cs.mana, cs.attack_damage, cs.ability_power, cs.armor, cs.magic_resist, 
         cs.attack_speed, cs.movement_speed;