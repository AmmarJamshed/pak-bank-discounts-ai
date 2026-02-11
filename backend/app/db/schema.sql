CREATE TABLE IF NOT EXISTS banks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    website VARCHAR(500) NOT NULL
);

CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    bank_id INTEGER NOT NULL REFERENCES banks(id),
    name VARCHAR(255) NOT NULL,
    tier VARCHAR(100),
    type VARCHAR(50) NOT NULL,
    CONSTRAINT uq_cards_bank_name UNIQUE (bank_id, name)
);

CREATE TABLE IF NOT EXISTS merchants (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category VARCHAR(150) NOT NULL,
    city VARCHAR(120) NOT NULL
);

CREATE TABLE IF NOT EXISTS discounts (
    id SERIAL PRIMARY KEY,
    merchant_id INTEGER NOT NULL REFERENCES merchants(id),
    card_id INTEGER NOT NULL REFERENCES cards(id),
    discount_percent FLOAT NOT NULL,
    conditions TEXT,
    valid_from DATE,
    valid_to DATE,
    CONSTRAINT uq_discount_unique UNIQUE (
        merchant_id, card_id, discount_percent, valid_from, valid_to
    )
);
