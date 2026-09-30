from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from db_config import DB_URL

CLEAN_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"

date_cols = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

tables = ["customers", "sellers", "payments", "orders",
          "order_items", "reviews", "products", "geolocation"]

engine = create_engine(DB_URL)

for name in tables:
    df = pd.read_csv(CLEAN_DIR / f"{name}_clean.csv", parse_dates=date_cols.get(name, []))
    df.to_sql(name, engine, if_exists="replace", index=False, chunksize=10000)
    print(f"Loaded {name}: {len(df)} rows")

print("\n--- Verify from database ---")
with engine.connect() as conn:
    for name in tables:
        n = conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar()
        print(f"{name}: {n}")