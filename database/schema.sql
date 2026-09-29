-- PostgreSQL Schema for RailGuard AI
-- Run this if you are using PostgreSQL instead of SQLite

CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    camera_id INTEGER DEFAULT 1,
    passenger_id INTEGER,
    train_state VARCHAR(50),
    danger_duration FLOAT,
    risk_level VARCHAR(20),
    reason VARCHAR(255),
    snapshot_path VARCHAR(255),
    status VARCHAR(20) DEFAULT 'OPEN'
);

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    incident_id INTEGER REFERENCES incidents(id),
    message VARCHAR(255),
    level VARCHAR(20)
);

CREATE INDEX idx_incidents_timestamp ON incidents(timestamp);
CREATE INDEX idx_incidents_risk ON incidents(risk_level);
