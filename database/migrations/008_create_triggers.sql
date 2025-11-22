-- Migration: Create Triggers
-- Auto-update timestamps and derived fields

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_transactions_updated_at ON transactions;
CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_reviews_updated_at ON reviews;
CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_survey_updated_at ON survey;
CREATE TRIGGER update_survey_updated_at BEFORE UPDATE ON survey
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_survey_sessions_updated_at ON survey_sessions;
CREATE TRIGGER update_survey_sessions_updated_at BEFORE UPDATE ON survey_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update review_count on products
CREATE OR REPLACE FUNCTION update_product_review_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE products
        SET review_count = review_count + 1
        WHERE item_id = NEW.item_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE products
        SET review_count = review_count - 1
        WHERE item_id = OLD.item_id;
    END IF
;
    RETURN NULL;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_update_review_count ON reviews;
CREATE TRIGGER trigger_update_review_count
AFTER INSERT OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION update_product_review_count();
