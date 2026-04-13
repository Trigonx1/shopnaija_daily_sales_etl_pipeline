# %%
import pandas as pd
import logging
import os
import numpy as np
import psycopg2
import requests
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from dotenv import load_dotenv

# %%
#load env variable
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

DB_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


# %%
# ── LOGGING CONFIG 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("shopnaija_pipeline.log"),
        logging.StreamHandler()
    ]
)

# %%
# ── DATE & FILE SETUP 
today = datetime.today()
yesterday = today - timedelta(days=1)
date_str = yesterday.strftime('%Y-%m-%d')
 
SALES_FILE = "sales_2026-04-06.csv"
API_FOLDER = "raw_data/api_raw"
API_FILE = f"{API_FOLDER}/exchange_rate.json"

# %%
# Ensure folders exist
os.makedirs("raw_data", exist_ok=True)
os.makedirs(API_FOLDER, exist_ok=True)

# %%
# EXTRACT

def extract_sales(filepath):
    try:
        logging.info(f"Reading sales file: {filepath}")
        df = pd.read_csv(filepath)
        logging.info(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")
        return df

    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return pd.DataFrame()

    except Exception as e:
        logging.error(f"Error reading sales data: {e}")
        return pd.DataFrame()

# %%
def extract_customers():
    try:
        logging.info("Connecting to database...")

        conn = psycopg2.connect (
            host= "aws-1-eu-north-1.pooler.supabase.com",
            port= 5432,
            database= "postgres",
            user= "postgres.mgfontepakyfahgoiejf",
            password= "choicetechky12345"
        )
        df = pd.read_sql("SELECT * FROM customers", conn)
        conn.close()

        logging.info(f"Customers loaded: {df.shape}")
        return df

    except Exception as e:
        logging.error(f"Error fetching customers: {e}")
        return pd.DataFrame()




# %%
def get_exchange_rate():
    try:
        logging.info("Fetching exchange rate...")

        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Save raw API response
        with open(API_FILE, "w") as f:
            json.dump(response.json(), f, indent=4)

        logging.info(f"Raw API saved: {API_FILE}")

        # Load from saved file
        with open(API_FILE, "r") as f:
            data = json.load(f)

        rate = data["rates"]["NGN"]
        logging.info(f"Exchange rate: {rate}")

        return rate

    except Exception as e:
        logging.error(f"Error fetching exchange rate: {e}")
        return None



# %%
#Transform

def transform(sales_df, customers_df, rate):
    logging.info("Starting transformation...")

    if sales_df.empty:
        logging.warning("Sales data is empty")
        return pd.DataFrame()
        
        # Clean column names
    sales_df.columns = sales_df.columns.str.lower().str.strip().str.replace(" ", "_")

    # Rename if needed
    if "price" in sales_df.columns:
        sales_df.rename(columns={"price": "unit_price_usd"}, inplace=True)

    # Handle missing values
    sales_df["quantity"] = sales_df["quantity"].fillna(0)
    sales_df["unit_price_usd"] = sales_df["unit_price_usd"].fillna(
        sales_df["unit_price_usd"].mean()
    )
    # Drop missing customer_id
    sales_df = sales_df.dropna(subset=["customer_id"])
    
    #  safe copy first
    sales_df = sales_df.copy()

    # Convert dates properly
    if "order_date" in sales_df.columns:
        sales_df.loc[:, "order_date"] = pd.to_datetime(
        sales_df["order_date"],
        dayfirst=True,
        errors="coerce"
        )
        # Merge
    
    final_df = pd.merge(
        sales_df,
        customers_df,
        on="customer_id",
        how="left"
    )
    # Feature engineering
    final_df["total_amount_usd"] = final_df["quantity"] * final_df["unit_price_usd"]

    if rate:
        final_df["total_amount_ngn"] = final_df["total_amount_usd"] * rate

    # Remove cancelled orders
    if "status" in final_df.columns:
        final_df = final_df[
            final_df["status"].str.strip().str.lower() != "cancelled"
        ]

    logging.info(f"Transformation complete: {final_df.shape}")
    return final_df



# %%
# VALIDATE
def validate(df):
    logging.info("Validating data...")

    if df.empty:
        logging.warning("No data to validate")
        return df

    if df.isnull().values.any():
        logging.warning("Null values detected")

    if (df["quantity"] <= 0).any():
        logging.warning("Invalid quantity detected")

    if (df["unit_price_usd"] <= 0).any():
        logging.warning("Invalid price detected")

    # Keep only valid rows
    valid_df = df[
        (df["quantity"] > 0) &
        (df["unit_price_usd"] > 0)
    ]

    logging.info(f"{len(valid_df)} rows ready for loading")
    return valid_df

# %%


def main():
    try:
        logging.info("Pipeline started")

        # Extract
        sales_df = extract_sales(SALES_FILE)
        customers_df = extract_customers()
        rate = get_exchange_rate()

        # Stop if critical data missing
        if sales_df.empty or customers_df.empty or rate is None:
            logging.error("Pipeline stopped due to missing data")
            return

        # Transform
        final_df = transform(sales_df, customers_df, rate)

        # Validate
        valid_df = validate(final_df)

        # Load
        load(valid_df, rate)

        logging.info("Pipeline completed successfully")

    except Exception as e:
        logging.error(f"Pipeline FAILED: {e}")
        raise


if __name__ == "__main__":
    main()

# %%



