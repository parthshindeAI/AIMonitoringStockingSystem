import pandas as pd
from prophet import Prophet
from pathlib import Path

def train_forecast_model(item_name='Wheat'):
    # Load cleaned data
    df = pd.read_csv("data/cleaned/cleaned_stock.csv")

    # Filter for one item
    item_df = df[df['item_name'] == item_name][['date', 'usage_today']]
    item_df = item_df.rename(columns={'date': 'ds', 'usage_today': 'y'})

    if item_df.shape[0] < 2:
        print("❌ Not enough data to train Prophet model.")
        return

    # Train the Prophet model
    model = Prophet()
    model.fit(item_df)

    # Make future predictions (next 7 days)
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)

    # Save the model + forecast
    forecast.to_csv(f"ml_model/{item_name}_forecast.csv", index=False)
    print(f"✅ Forecast for '{item_name}' saved to ml_model/{item_name}_forecast.csv")

if __name__ == "__main__":
    train_forecast_model('Wheat')  # Change item as needed
