import streamlit as st
import pandas as pd
import os
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, func
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import plotly.graph_objects as go

# --- STREAMLIT UI ---

st.set_page_config(
    page_title="StockWiseAI – Grocery Stock Tracker",
    page_icon="🛒",
    layout="wide"
)

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3075/3075977.png", width=100)
    st.title("GROUP-3")
    st.markdown("##### Smart Grocery Stock Tracker")
    st.markdown("Built by: Parth, Manoj, Kavya, Aadit")
    st.markdown("🔗 [GitHub Repo](https://github.com/parthshindeAI/AIMonitoringStockingSystem.git)")
    st.markdown("📆 Review Date: 13 Aug 2025")
    st.markdown("---")

# --- MAIN TITLE ---
st.title("🧾 Grocery Stock Monitoring Dashboard")
st.markdown("Welcome to your AI-powered grocery inventory system. Log usage, view forecasts, and stay restocked — effortlessly.")
st.markdown("----")


# --- SETUP ---

# SQLite DB setup
DB_PATH = "sqlite:///database/grocery_stock.db"
engine = create_engine(DB_PATH)
Session = sessionmaker(bind=engine)
session = Session()

# SQLAlchemy base
Base = declarative_base()

# --- DEFINE TABLES ---

class Item(Base):
    __tablename__ = 'Items'
    id = Column(Integer, primary_key=True)
    item_name = Column(String, nullable=False)
    category = Column(String, nullable=False)

class StockLog(Base):
    __tablename__ = 'StockLogs'
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('Items.id'))
    current_stock = Column(Integer, nullable=False)
    usage_today = Column(Integer, nullable=False)
    damaged_stock = Column(Integer)
    delivery_quantity = Column(Integer)
    date = Column(String, nullable=False)

class FeedbackLog(Base):
    __tablename__ = 'FeedbackLogs'
    id = Column(Integer, primary_key=True)
    item_name = Column(String, nullable=False)
    feedback_type = Column(String, nullable=False)  # e.g., 'forecast', 'anomaly'
    feedback_value = Column(String, nullable=False) # e.g., 'agree', 'disagree'
    date = Column(String, nullable=False)


# --- HELPER FUNCTION: Fetch current stock from DB ---

def get_current_stock():
    result = (
        session.query(
            Item.item_name,
            Item.category,
            func.max(StockLog.date).label("last_updated"),
            func.sum(StockLog.current_stock).label("total_stock")
        )
        .join(StockLog, Item.id == StockLog.item_id)
        .group_by(Item.item_name, Item.category)
        .all()
    )

    stock_data = pd.DataFrame(result, columns=["Item", "Category", "Last Updated", "Total Stock"])
    return stock_data

# Create tables if they don't exist
Base.metadata.create_all(engine)

# --- STREAMLIT UI ---
# --- ENTRY FORM POLISHED ---

with st.expander("📥 Log Today's Stock Entry", expanded=True):
    st.subheader("🧾 Grocery Stock Entry Form")

    col1, col2 = st.columns(2)

    with col1:
        item_name = st.text_input("🛒 Item Name")
        category = st.selectbox("📂 Category", ["Grains", "Snacks", "Dairy", "Beverages", "Vegetables", "Fruits", "Frozen"])
        current_stock = st.number_input("📦 Current Stock (units)", min_value=0)
        usage_today = st.number_input("📉 Used Today", min_value=0)

    with col2:
        damaged_stock = st.number_input("🗑️ Damaged/Expired", min_value=0)
        delivery_quantity = st.number_input("🚚 Delivered Today", min_value=0)
        entry_date = st.date_input("📅 Date", value=date.today())

if st.button("Submit Entry"):
    if item_name.strip() == "":
        st.warning("Item name is required!")
    else:
        normalized_item_name = item_name.strip().lower()

        # Check if item already exists (case-insensitive)
        item = session.query(Item).filter(
            func.lower(Item.item_name) == normalized_item_name,
            Item.category == category
        ).first()

        if not item:
            item = Item(item_name=normalized_item_name, category=category)
            session.add(item)
            session.commit()

        # Add stock log
        stock_log = StockLog(
            item_id=item.id,
            current_stock=current_stock,
            usage_today=usage_today,
            damaged_stock=damaged_stock,
            delivery_quantity=delivery_quantity,
            date=entry_date.strftime("%Y-%m-%d")
        )
        session.add(stock_log)
        try:
            session.commit()
            st.success("✅ Entry saved to database!")
            st.write("Here’s what was stored:")
            st.write(pd.DataFrame([{
                "Item": normalized_item_name.capitalize(),
                "Category": category,
                "Current Stock": current_stock,
                "Used Today": usage_today,
                "Damaged": damaged_stock,
                "Delivered": delivery_quantity,
                "Date": entry_date
            }]))
        except IntegrityError:
            session.rollback()
            st.error("❌ Failed to save entry!")

# --- FORECAST SECTION ---

st.markdown("---")
with st.expander("🔮 Forecast & Stock Insights", expanded=True):
    st.subheader("📊 Forecast & Runout Prediction")

    # Get all items that have a trained forecast CSV
    available_items = [
        f.split("_forecast.csv")[0].capitalize()
        for f in os.listdir("ml_model")
        if f.endswith("_forecast.csv")
    ]

    if available_items:
        item_to_view = st.selectbox("📌 Select item to view forecast", sorted(available_items))

        if st.button("Generate Forecast"):
            try:
                forecast_path = f"ml_model/{item_to_view.lower()}_forecast.csv"
                forecast_df = pd.read_csv(forecast_path)

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=forecast_df['ds'],
                    y=forecast_df['yhat'],
                    mode='lines+markers',
                    name='Forecast'
                ))

                fig.update_layout(
                    title=f"{item_to_view} Usage Forecast",
                    xaxis_title="Date",
                    yaxis_title="Expected Daily Usage",
                    template="plotly_white"
                )

                st.plotly_chart(fig, use_container_width=True)

                # Show predicted runout date (when yhat crosses a low threshold)
                runout = forecast_df[forecast_df['yhat'] < 1]
                if not runout.empty:
                    runout_date = runout.iloc[0]['ds']
                    st.warning(f"⚠️ Predicted runout date for {item_to_view}: **{runout_date}**")
                else:
                    st.success("✅ No stock depletion expected in the next 7 days.")

                # --- Feedback Buttons for Forecast ---
                st.markdown("#### 🗣️ Was this forecast accurate?")
                col1, col2 = st.columns(2)

                if col1.button("👍 Agree with Forecast"):
                    session.add(FeedbackLog(
                        item_name=item_to_view,
                        feedback_type='forecast',
                        feedback_value='agree',
                        date=str(date.today())
                    ))
                    session.commit()
                    st.success("Thanks for your feedback! 👍")

                if col2.button("👎 Disagree with Forecast"):
                    session.add(FeedbackLog(
                        item_name=item_to_view,
                        feedback_type='forecast',
                        feedback_value='disagree',
                        date=str(date.today())
                    ))
                    session.commit()
                    st.warning("Feedback noted. We'll review the prediction. 👀")

            except FileNotFoundError:
                st.error(f"❌ Forecast for {item_to_view} not found. Please train the model first.")
    else:
        st.info("ℹ️ No forecast files available. Train model to generate predictions.")

# --- ANOMALY ALERT SYSTEM ---

with st.expander("🔔 Anomaly Detection & Alerts", expanded=True):
    st.subheader("🚨 AI-Driven Anomaly Alerts")

    try:
        anomaly_df = pd.read_csv("data/cleaned/anomaly_output.csv")
    except FileNotFoundError:
        st.warning("⚠️ No anomaly data found. Please run the detector first.")
        anomaly_df = pd.DataFrame()

    if not anomaly_df.empty:
        anomalies = anomaly_df[anomaly_df['anomaly'] == 'Anomaly']

        if anomalies.empty:
            st.success("✅ No anomalies detected! All usage is within normal range.")
        else:
            st.error(f"🚨 {len(anomalies)} anomalies detected!")

            # 📈 Optional Chart: Visualize usage with anomalies
            import plotly.graph_objects as go
            anomaly_df["date"] = pd.to_datetime(anomaly_df["date"])
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=anomaly_df["date"],
                y=anomaly_df["usage_today"],
                mode='lines+markers',
                name="Usage Trend",
                line=dict(color='blue')
            ))

            anomaly_points = anomaly_df[anomaly_df['anomaly'] == 'Anomaly']
            fig.add_trace(go.Scatter(
                x=anomaly_points["date"],
                y=anomaly_points["usage_today"],
                mode='markers',
                name="Anomalies",
                marker=dict(color='red', size=10, symbol="x")
            ))

            fig.update_layout(title="📉 Usage Trend with Anomalies",
                              xaxis_title="Date", yaxis_title="Usage",
                              showlegend=True)

            st.plotly_chart(fig, use_container_width=True)

            # 📋 Table of Anomalies
            st.dataframe(anomalies[['date', 'usage_today']])

            for _, row in anomalies.iterrows():
                st.warning(f"⚠️ Suspicious usage on {row['date'].strftime('%Y-%m-%d')} → {row['usage_today']} units used.")

            # 🗳️ Feedback Buttons
            st.markdown("#### Do you agree with these anomalies?")
            col3, col4 = st.columns(2)

            if col3.button("👍 Agree with Anomalies"):
                session.add(FeedbackLog(
                    item_name="general",
                    feedback_type='anomaly',
                    feedback_value='agree',
                    date=str(date.today())
                ))
                session.commit()
                st.success("Thanks for confirming the anomalies!")

            if col4.button("👎 Disagree with Anomalies"):
                session.add(FeedbackLog(
                    item_name="general",
                    feedback_type='anomaly',
                    feedback_value='disagree',
                    date=str(date.today())
                ))
                session.commit()
                st.warning("We'll analyze the detection logic. Thank you!")

    else:
        st.info("ℹ️ Upload or generate anomaly data to view alerts.")


# --- LIVE STOCK DASHBOARD ---
with st.expander("📦 Current Stock Dashboard", expanded=True):
    st.subheader("📊 Live Inventory Overview")

    stock_df = get_current_stock()

    if not stock_df.empty:
        # Add emoji tags by category (optional spice 🌶️)
        emoji_map = {
            "Grains": "🌾",
            "Snacks": "🍪",
            "Dairy": "🧀",
            "Beverages": "🥤",
            "Vegetables": "🥦",
            "Fruits": "🍎",
            "Frozen": "❄️"
        }

        stock_df["Category"] = stock_df["Category"].map(lambda x: f"{emoji_map.get(x, '')} {x}")
        stock_df["Last Updated"] = pd.to_datetime(stock_df["Last Updated"]).dt.strftime("%Y-%m-%d")

        st.markdown(f"📌 **Total unique items tracked:** `{len(stock_df)}`")

        # Highlight low stock items
        low_stock_threshold = 5
        def highlight_low_stock(val):
            return 'background-color: #ffe6e6' if val < low_stock_threshold else ''

        st.dataframe(
            stock_df.style.applymap(highlight_low_stock, subset=["Total Stock"]),
            use_container_width=True
        )

    else:
        st.info("🚫 No stock entries yet. Start logging items above to see them here.")


# --- DAILY USAGE TREND ---
# --- DAILY USAGE TRENDS ---
st.markdown("---")
with st.expander("📉 Daily Usage Trends", expanded=True):
    st.subheader("📊 Track Usage Over Time")

    # Fetch distinct normalized item names
    item_names = session.query(Item.item_name).distinct().all()
    item_names = sorted(set(name[0].capitalize() for name in item_names))

    selected_trend_item = st.selectbox("Select item to view usage trend", item_names)

    if selected_trend_item:
        item_obj = session.query(Item).filter(func.lower(Item.item_name) == selected_trend_item.lower()).first()

        if item_obj:
            usage_data = (
                session.query(StockLog.date, StockLog.usage_today)
                .filter_by(item_id=item_obj.id)
                .order_by(StockLog.date)
                .all()
            )

            if usage_data:
                trend_df = pd.DataFrame(usage_data, columns=["Date", "Usage"])
                trend_df["Date"] = pd.to_datetime(trend_df["Date"])

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=trend_df["Date"],
                    y=trend_df["Usage"],
                    mode="lines+markers",
                    name="Usage Over Time",
                    line=dict(color="dodgerblue")
                ))

                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Units Used",
                    title=f"📈 Daily Usage Trend for {selected_trend_item}",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ No usage data available for this item yet.")
        else:
            st.error("❌ Item not found in database.")

# --- FEEDBACK LOG VIEW ---
st.markdown("---")
with st.expander("🗣️ Feedback Log", expanded=False):
    st.subheader("📥 User Feedback Summary")

    feedbacks = session.query(FeedbackLog).all()

    if feedbacks:
        feedback_df = pd.DataFrame([
            (f.item_name.capitalize(), f.feedback_type.capitalize(), f.feedback_value.capitalize(), f.date)
            for f in feedbacks
        ], columns=["Item", "Type", "Response", "Date"])

        st.dataframe(feedback_df)
    else:
        st.info("No feedback submitted yet.")
