import pandas as pd
from pathlib import Path

def run_etl():
    # Load raw data
    raw_path = Path("data/raw/grocery_stock_log.csv")
    df = pd.read_csv(raw_path)

    print("✅ Raw data loaded")

    # Clean data
    df.drop_duplicates(inplace=True)
    df.dropna(inplace=True)
    df['date'] = pd.to_datetime(df['date'])

    # Normalize units (dummy - you can expand later)
    df['current_stock'] = df['current_stock'].astype(int)
    df['usage_today'] = df['usage_today'].astype(int)

    # Save cleaned data
    cleaned_path = Path("data/cleaned")
    cleaned_path.mkdir(parents=True, exist_ok=True)
    df.to_csv(cleaned_path / "cleaned_stock.csv", index=False)

    print("✅ Cleaned data saved at:", cleaned_path / "cleaned_stock.csv")

if __name__ == "__main__":
    run_etl()
