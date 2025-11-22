-- Migration: Enable Row Level Security (RLS)
-- Basic policies - adjust based on your auth strategy

-- Enable RLS on all tables
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_sessions ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read access to products (public catalog)
DROP POLICY IF EXISTS "Allow public read access to products" ON products;
CREATE POLICY "Allow public read access to products"
ON products FOR SELECT
TO anon
USING (true);

-- Users can only view their own data
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
CREATE POLICY "Users can view their own profile"
ON users FOR SELECT
TO authenticated
USING (auth.uid()::uuid = user_id);

-- Users can only view their own transactions
DROP POLICY IF EXISTS "Users can view their own transactions" ON transactions;
CREATE POLICY "Users can view their own transactions"
ON transactions FOR SELECT
TO authenticated
USING (user_id = auth.uid()::uuid);

-- Users can view and create their own reviews
DROP POLICY IF EXISTS "Users can view their own reviews" ON reviews;
CREATE POLICY "Users can view their own reviews"
ON reviews FOR SELECT
TO authenticated
USING (user_id = auth.uid()::uuid);

DROP POLICY IF EXISTS "Users can create their own reviews" ON reviews;
CREATE POLICY "Users can create their own reviews"
ON reviews FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid()::uuid);

-- Users can view their own survey questions
DROP POLICY IF EXISTS "Users can view their own survey questions" ON survey;
CREATE POLICY "Users can view their own survey questions"
ON survey FOR SELECT
TO authenticated
USING (user_id = auth.uid()::uuid);

-- Users can view their own survey sessions
DROP POLICY IF EXISTS "Users can view their own survey sessions" ON survey_sessions;
CREATE POLICY "Users can view their own survey sessions"
ON survey_sessions FOR SELECT
TO authenticated
USING (user_id = auth.uid()::uuid);
