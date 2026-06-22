

DROP TABLE IF EXISTS claims CASCADE;
DROP TABLE IF EXISTS food_listings CASCADE;
DROP TABLE IF EXISTS receivers CASCADE;
DROP TABLE IF EXISTS providers CASCADE;

CREATE TABLE providers (
    provider_id   INTEGER PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    type          VARCHAR(100),
    address       TEXT,
    city          VARCHAR(150),
    contact       VARCHAR(100)
);

CREATE TABLE receivers (
    receiver_id   INTEGER PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    type          VARCHAR(100),
    city          VARCHAR(150),
    contact       VARCHAR(100)
);

CREATE TABLE food_listings (
    food_id        INTEGER PRIMARY KEY,
    food_name      VARCHAR(255) NOT NULL,
    quantity        INTEGER NOT NULL CHECK (quantity >= 0),
    expiry_date     DATE,
    provider_id     INTEGER REFERENCES providers(provider_id) ON DELETE CASCADE,
    provider_type   VARCHAR(100),
    location        VARCHAR(150),
    food_type       VARCHAR(50),
    meal_type        VARCHAR(50)
);

CREATE TABLE claims (
    claim_id      INTEGER PRIMARY KEY,
    food_id       INTEGER REFERENCES food_listings(food_id) ON DELETE CASCADE,
    receiver_id   INTEGER REFERENCES receivers(receiver_id) ON DELETE CASCADE,
    status        VARCHAR(20) NOT NULL CHECK (status IN ('Pending', 'Completed', 'Cancelled')),
    timestamp     TIMESTAMP NOT NULL
);

CREATE INDEX idx_food_provider ON food_listings(provider_id);
CREATE INDEX idx_food_city ON food_listings(location);
CREATE INDEX idx_claims_food ON claims(food_id);
CREATE INDEX idx_claims_receiver ON claims(receiver_id);
CREATE INDEX idx_claims_status ON claims(status);
