CREATE TABLE IF NOT EXISTS ministry_mapping (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    normalized_title TEXT NOT NULL UNIQUE,
    mp_id INTEGER NOT NULL REFERENCES mps(id),
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_ministry_mapping_title ON ministry_mapping(normalized_title);

INSERT OR REPLACE INTO ministry_mapping (normalized_title, mp_id)
SELECT 'minister of finance', id FROM mps WHERE name = 'Ndaba Gaolathe';

INSERT OR REPLACE INTO ministry_mapping (normalized_title, mp_id)
SELECT 'minister for state president defence and security', id FROM mps WHERE name = 'Moeti Mohwasa';

INSERT OR REPLACE INTO ministry_mapping (normalized_title, mp_id)
SELECT 'minister of state presidency', id FROM mps WHERE name = 'Moeti Mohwasa';

INSERT OR REPLACE INTO ministry_mapping (normalized_title, mp_id)
SELECT 'minister of labour and home affairs', id FROM mps WHERE name = 'Pius Mokgware';

INSERT OR REPLACE INTO ministry_mapping (normalized_title, mp_id)
SELECT 'minister of sport and arts', id FROM mps WHERE name = 'Jacob Kelebeng';

INSERT OR REPLACE INTO ministry_mapping (normalized_title, mp_id)
SELECT 'minister of sports and arts', id FROM mps WHERE name = 'Jacob Kelebeng';
