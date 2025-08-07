import streamlit as st
import pandas as pd
import os
from datetime import date
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import exists

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

# Create tables if they don't exist
Base.metadata.create_all(engine)

# --- STREAMLIT UI ---

st.title("🧾 Grocery Stock Entry Form")

categories = ["Grains", "Snacks", "Dairy", "Beverages", "Vegetables", "Fruits", "Frozen"]

item_name = st.text_input("Item Name")
category = st.selectbox("Category", categories)
current_stock = st.number_input("Current Stock (units)", min_value=0)
usage_today = st.number_input("Used Today", min_value=0)
damaged_stock = st.number_input("Damaged/Expired", min_value=0)
delivery_quantity = st.number_input("Delivered Today", min_value=0)
entry_date = st.date_input("Date", value=date.today())

if st.button("Submit Entry"):
    if item_name.strip() == "":
        st.warning("Item name is required!")
    else:
        # Check if item already exists
        item = session.query(Item).filter_by(item_name=item_name, category=category).first()
        if not item:
            item = Item(item_name=item_name, category=category)
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
                "Item": item_name,
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
