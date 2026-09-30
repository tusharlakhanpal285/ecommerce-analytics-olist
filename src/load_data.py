from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

files = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

def load_all():
    return {name: pd.read_csv(DATA_DIR / fname) for name, fname in files.items()}

if __name__ == "__main__":
    data = load_all()
    for name, df in data.items():
        print(f"\n=== {name} === shape: {df.shape}")
        nulls = df.isnull().sum()
        print(nulls[nulls > 0])
        print(df.head(2))