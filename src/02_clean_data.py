from pathlib import Path
import pandas as pd
from load_data import load_all

CLEAN_DIR = Path(__file__).resolve().parent.parent / "data" / "clean"
CLEAN_DIR.mkdir(exist_ok=True)


def clean_orders(orders):
    date_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    for col in date_cols:
        orders[col] = pd.to_datetime(orders[col])

    orders["delivery_days"] = (
        orders["order_delivered_customer_date"] - orders["order_purchase_timestamp"]
    ).dt.days
    orders["delay_days"] = (
        orders["order_delivered_customer_date"] - orders["order_estimated_delivery_date"]
    ).dt.days
    return orders


def clean_order_items(items):
    items["shipping_limit_date"] = pd.to_datetime(items["shipping_limit_date"])
    return items


def clean_reviews(reviews):
    reviews["review_creation_date"] = pd.to_datetime(reviews["review_creation_date"])
    reviews["review_answer_timestamp"] = pd.to_datetime(reviews["review_answer_timestamp"])
    reviews = reviews.sort_values("review_answer_timestamp").drop_duplicates(
        subset="order_id", keep="last"
    )
    return reviews


def clean_products(products, translation):
    products = products.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })
    products = products.merge(translation, on="product_category_name", how="left")
    products["product_category_name_english"] = (
        products["product_category_name_english"]
        .fillna(products["product_category_name"])
        .fillna("unknown")
    )
    return products


def clean_geolocation(geo):
    return geo.groupby("geolocation_zip_code_prefix", as_index=False).agg(
        geolocation_lat=("geolocation_lat", "mean"),
        geolocation_lng=("geolocation_lng", "mean"),
    )


if __name__ == "__main__":
    data = load_all()

    print("--- Duplicate rows (poori row same) ---")
    for name, df in data.items():
        print(f"{name}: {df.duplicated().sum()}")

    clean = {
        "customers": data["customers"],
        "sellers": data["sellers"],
        "payments": data["payments"],
        "orders": clean_orders(data["orders"]),
        "order_items": clean_order_items(data["order_items"]),
        "reviews": clean_reviews(data["reviews"]),
        "products": clean_products(data["products"], data["category_translation"]),
        "geolocation": clean_geolocation(data["geolocation"]),
    }

    print("\n--- Before -> After (rows) ---")
    for name, df in clean.items():
        print(f"{name}: {len(data[name])} -> {len(df)}")

    print("\n--- Order status counts ---")
    print(clean["orders"]["order_status"].value_counts())

    print("\n--- Products: null check ---")
    print(clean["products"].isnull().sum()[lambda s: s > 0])

    for name, df in clean.items():
        df.to_csv(CLEAN_DIR / f"{name}_clean.csv", index=False)
    print("\nSaved cleaned files in data/clean/")