from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # window kholne ki jagah seedha file mein save
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from db_config import DB_URL

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)

engine = create_engine(DB_URL)

# 1. Har unique customer ka last purchase, order count aur total spend (SQL se)
query = """
SELECT c.customer_unique_id,
       MAX(o.order_purchase_timestamp) AS last_purchase,
       COUNT(DISTINCT o.order_id) AS frequency,
       SUM(oi.price) AS monetary
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id
"""
df = pd.read_sql(query, engine)

# 2. Recency: dataset ki aakhri date ke ek din baad se kitne din pehle purchase hui
df["last_purchase"] = pd.to_datetime(df["last_purchase"])
snapshot = df["last_purchase"].max() + pd.Timedelta(days=1)
df["recency"] = (snapshot - df["last_purchase"]).dt.days

# 3. Scores 1-5 (5 = best). Recency mein kam din = better, isliye labels ulte
df["R"] = pd.qcut(df["recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
df["M"] = pd.qcut(df["monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)

# 4. Segments. Frequency pe qcut nahi lagaya kyunki ~97% customers ke 1 hi order hain,
#    isliye segments R, M aur "repeat ya nahi" pe bane hain. Upar wali condition pehle match hoti hai.
conditions = [
    (df["frequency"] >= 2) & (df["R"] >= 4),
    (df["frequency"] >= 2),
    (df["R"] >= 4),
    (df["M"] >= 4),
    (df["R"] <= 2),
]
labels = ["Champions", "Loyal", "Recent One-Time", "High-Value At Risk", "Lost"]
df["segment"] = np.select(conditions, labels, default="Need Attention")

# 5. Segment summary
summary = df.groupby("segment").agg(
    customers=("customer_unique_id", "count"),
    avg_recency_days=("recency", "mean"),
    avg_orders=("frequency", "mean"),
    avg_spend=("monetary", "mean"),
    total_revenue=("monetary", "sum"),
)
summary["customers_pct"] = 100 * summary["customers"] / summary["customers"].sum()
summary["revenue_pct"] = 100 * summary["total_revenue"] / summary["total_revenue"].sum()
summary = summary.sort_values("total_revenue", ascending=False).round(1)

print(summary.to_string())
print(f"\nRepeat customers (2+ orders): {(df['frequency'] >= 2).mean() * 100:.1f}%")

summary.to_csv(OUT_DIR / "rfm_summary.csv")
df.to_csv(OUT_DIR / "rfm_customers.csv", index=False)

# 6. Chart: customers vs revenue by segment
fig, ax = plt.subplots(1, 2, figsize=(13, 5))
summary["customers"].plot.barh(ax=ax[0], color="#4C78A8")
ax[0].set_title("Customers by Segment")
ax[0].invert_yaxis()
summary["total_revenue"].plot.barh(ax=ax[1], color="#F58518")
ax[1].set_title("Revenue by Segment (BRL)")
ax[1].invert_yaxis()
plt.tight_layout()
plt.savefig(OUT_DIR / "rfm_segments.png", dpi=150)
print("Saved chart and CSVs in outputs/")