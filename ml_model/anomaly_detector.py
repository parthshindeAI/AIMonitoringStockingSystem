import pandas as pd
from sklearn.ensemble import IsolationForest
from pathlib import Path

def detect_anomalies(item_name='Wheat'):
    path = Path("data/cleaned/cleaned_stock.csv")
    df = pd.read_csv(path)

    # Filter for selected item
    item_df = df[df['item_name'] == item_name][['date', 'usage_today']]

    if item_df.shape[0] < 5:
        print("⚠️ Not enough data for anomaly detection.")
        return pd.DataFrame()

    # Prepare data
    item_df['date'] = pd.to_datetime(item_df['date'])
    item_df = item_df.sort_values('date')
    item_df['usage_today'] = item_df['usage_today'].astype(float)

    # Isolation Forest
    model = IsolationForest(contamination=0.2, random_state=42)
    item_df['anomaly'] = model.fit_predict(item_df[['usage_today']])
    item_df['anomaly'] = item_df['anomaly'].map({1: 'Normal', -1: 'Anomaly'})

    print(f"✅ Anomaly detection done for {item_name}")
    return item_df

if __name__ == "__main__":
    df_result = detect_anomalies("Wheat")

    if not df_result.empty:
        # Save it to CSV
        output_path = "data/cleaned/anomaly_output.csv"
        df_result.to_csv(output_path, index=False)
        print(f"✅ Anomaly results saved to {output_path}")
    else:
        print("⚠️ Not enough data to generate anomaly file.")
