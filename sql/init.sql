-- 1. Metadata Table
CREATE TABLE IF NOT EXISTS stocks (
    ticker VARCHAR(10) PRIMARY KEY,
    company_name VARCHAR(255),
    sector VARCHAR(100),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Price Logs Table
CREATE TABLE IF NOT EXISTS price_logs (
    id BIGSERIAL PRIMARY KEY,
    ticker VARCHAR(10) REFERENCES stocks(ticker) ON DELETE CASCADE,
    price NUMERIC(15, 4) NOT NULL,
    volume BIGINT,
    captured_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. High-Performance Indexes
CREATE INDEX IF NOT EXISTS idx_captured_at ON price_logs (captured_at);
CREATE INDEX IF NOT EXISTS idx_ticker_captured ON price_logs (ticker, captured_at DESC);

-- 4. The Analysis View (OHLC)
CREATE OR REPLACE VIEW daily_summary AS
SELECT 
    ticker,
    DATE(captured_at) as trade_date,
    (ARRAY_AGG(price ORDER BY captured_at ASC))[1] as open,
    MAX(price) as high,
    MIN(price) as low,
    (ARRAY_AGG(price ORDER BY captured_at DESC))[1] as close,
    SUM(volume) as total_volume
FROM price_logs
GROUP BY ticker, DATE(captured_at);