CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS route_searches (
  id BIGSERIAL PRIMARY KEY,
  user_hash VARCHAR(96) NOT NULL,
  source GEOGRAPHY(POINT, 4326) NOT NULL,
  destination GEOGRAPHY(POINT, 4326) NOT NULL,
  priority VARCHAR(32) NOT NULL,
  selected_route_id VARCHAR(64),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS road_segments (
  segment_id VARCHAR(64) PRIMARY KEY,
  name TEXT,
  road_class VARCHAR(32),
  speed_limit_kph NUMERIC,
  geom GEOGRAPHY(LINESTRING, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS segment_observations (
  observed_at TIMESTAMPTZ NOT NULL,
  segment_id VARCHAR(64) NOT NULL REFERENCES road_segments(segment_id),
  avg_speed_kph NUMERIC NOT NULL,
  travel_time_seconds NUMERIC NOT NULL,
  congestion_index NUMERIC NOT NULL CHECK (congestion_index BETWEEN 0 AND 1),
  sample_count INTEGER NOT NULL DEFAULT 1
);

SELECT create_hypertable('segment_observations', 'observed_at', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS incidents (
  id BIGSERIAL PRIMARY KEY,
  kind VARCHAR(32) NOT NULL,
  severity NUMERIC NOT NULL CHECK (severity BETWEEN 0 AND 1),
  location GEOGRAPHY(POINT, 4326) NOT NULL,
  description TEXT,
  source VARCHAR(64) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_route_searches_created_at ON route_searches(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_location ON incidents USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_road_segments_geom ON road_segments USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_segment_observations_segment_time ON segment_observations(segment_id, observed_at DESC);

