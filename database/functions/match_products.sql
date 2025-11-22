-- Function for vector similarity search on products
-- Used by Agent 1 to find similar products

CREATE OR REPLACE FUNCTION match_products(
  query_embedding vector(1536),
  match_threshold float DEFAULT 0.7,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  item_id uuid,
  source_platform varchar,
  product_url text,
  title text,
  brand varchar,
  category varchar,
  price numeric,
  description text,
  embedding vector(1536),
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    p.item_id,
    p.source_platform,
    p.product_url,
    p.title,
    p.brand,
    p.category,
    p.price,
    p.description,
    p.embedding,
    1 - (p.embedding <=> query_embedding) AS similarity
  FROM products p
  WHERE 1 - (p.embedding <=> query_embedding) > match_threshold
  ORDER BY p.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Add comment
COMMENT ON FUNCTION match_products IS 'Find similar products using cosine similarity on embeddings';
