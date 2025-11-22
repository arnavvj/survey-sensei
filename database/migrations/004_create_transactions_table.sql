-- Migration: Create TRANSACTIONS table
-- Stores purchase and delivery information

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES products(item_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Transaction details
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    delivery_date TIMESTAMP WITH TIME ZONE,
    expected_delivery_date TIMESTAMP WITH TIME ZONE,
    return_date TIMESTAMP WITH TIME ZONE,

    -- Pricing
    original_price DECIMAL(12, 2) NOT NULL,
    retail_price DECIMAL(12, 2) NOT NULL,
    discount_percentage DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE
            WHEN original_price > 0 THEN ((original_price - retail_price) / original_price * 100)
            ELSE 0
        END
    ) STORED,

    -- Status tracking
    transaction_status VARCHAR(50) DEFAULT 'pending', -- pending, delivered, returned, cancelled

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_delivery_date CHECK (delivery_date IS NULL OR delivery_date >= order_date),
    CONSTRAINT check_return_date CHECK (return_date IS NULL OR return_date >= delivery_date),
    CONSTRAINT check_prices CHECK (original_price >= 0 AND retail_price >= 0)
);

-- Indexes for transactions
CREATE INDEX IF NOT EXISTS idx_transactions_item_id ON transactions(item_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_order_date ON transactions(order_date);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(transaction_status);

-- Comments
COMMENT ON TABLE transactions IS 'Purchase and delivery tracking';
