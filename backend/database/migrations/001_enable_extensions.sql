-- Migration: Enable PostgreSQL Extensions
-- Required extensions for Survey Sensei

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vector embeddings (pgvector)
CREATE EXTENSION IF NOT EXISTS "vector";
