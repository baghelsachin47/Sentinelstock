import asyncio

import pandas as pd
import yfinance as yf
from psycopg2.extras import execute_values

from database import get_connection

# Added BTC-USD for 24/7 data testing
TICKERS = ["AAPL", "TSLA", "MSFT", "GOOGL", "AMZN", "BTC-USD"]


async def sync_metadata(conn):
    """Fetches basic company info and ensures the stocks table is populated."""
    print("Syncing stock metadata...")
    with conn.cursor() as cur:
        for t in TICKERS:
            try:
                # yfinance info can sometimes be slow, so we thread it
                info = await asyncio.to_thread(lambda: yf.Ticker(t).info)
                name = info.get("longName", t)
                sector = info.get("sector", "Crypto" if "-" in t else "N/A")
            except Exception:
                # Fallback if yfinance metadata fails
                name = t
                sector = "Crypto" if "-" in t else "N/A"

            cur.execute(
                """
                INSERT INTO stocks (ticker, company_name, sector)
                VALUES (%s, %s, %s)
                ON CONFLICT (ticker) DO UPDATE SET last_updated = NOW()
            """,
                (t, name, sector),
            )
    conn.commit()
    print("Metadata synced successfully.")


async def main():
    # 1. Establish connection using your robust database.py logic
    conn = get_connection()
    if not conn:
        print("Exiting Ingestor: Could not establish database connection.")
        return

    try:
        # 2. Sync Metadata First
        await sync_metadata(conn)

        # 3. Enter the continuous fetching loop
        print("Starting real-time data ingestion...")
        while True:
            try:
                # Download 1-minute interval data for all tickers
                data = await asyncio.to_thread(
                    yf.download,
                    tickers=TICKERS,
                    period="1d",
                    interval="1m",
                    group_by="ticker",
                    progress=False,
                )

                logs = []
                for t in TICKERS:
                    if not data[t].empty:
                        latest = data[t].iloc[-1]

                        # Safely handle the Close price
                        close_price = float(latest["Close"])

                        # Safely handle missing (NaN) Crypto volume
                        raw_vol = latest["Volume"]
                        safe_vol = 0 if pd.isna(raw_vol) else int(raw_vol)

                        logs.append((t, close_price, safe_vol))

                # 4. Batch Insert into PostgreSQL
                if logs:
                    with conn.cursor() as cur:
                        execute_values(
                            cur,
                            "INSERT INTO price_logs (ticker, price, volume) VALUES %s",
                            logs,
                        )
                    conn.commit()
                    print(f"Logged {len(logs)} updates.")

            except Exception as e:
                print(f"Loop Error: {e}")

            # Wait 60 seconds before fetching the next minute's candle
            await asyncio.sleep(60)

    except KeyboardInterrupt:
        print("\nStopping ingestor gracefully...")
    finally:
        # Always close the connection when the script stops
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
