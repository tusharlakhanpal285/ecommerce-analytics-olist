from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine
from db_config import DB_URL

OUT_DIR = Path(__file__).resolve().parent.parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)
engine = create_engine(DB_URL)


def run(q):
    return pd.read_sql(q, engine)


# 1. Monthly revenue (2017-01 se 2018-08: pehle aur baad ke mahine bahut chhote/adhoore hain)
monthly = run("""
SELECT TO_CHAR(DATE_TRUNC('month', o.order_purchase_timestamp), 'YYYY-MM') AS month,
       SUM(oi.price) AS revenue
FROM orders o JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1 ORDER BY 1
""")
monthly = monthly[(monthly["month"] >= "2017-01") & (monthly["month"] <= "2018-08")]
print("\n--- Monthly revenue ---")
print(monthly.round(0).to_string(index=False))

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(monthly["month"], monthly["revenue"], marker="o", color="#4C78A8")
ax.set_title("Monthly Revenue (Delivered Orders)")
ax.set_ylabel("Revenue (BRL)")
ax.set_xticks(range(0, len(monthly), 2))
ax.set_xticklabels(monthly["month"].iloc[::2], rotation=45)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(OUT_DIR / "monthly_revenue.png", dpi=150)
plt.close()

# 2. Top 10 categories
cats = run("""
SELECT p.product_category_name_english AS category,
       SUM(oi.price) AS revenue,
       100 * SUM(oi.price) / SUM(SUM(oi.price)) OVER () AS share_pct
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY 1 ORDER BY revenue DESC LIMIT 10
""")
print("\n--- Top 10 categories ---")
print(cats.round(1).to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(cats["category"], cats["revenue"], color="#F58518")
ax.invert_yaxis()
ax.set_title("Top 10 Categories by Revenue")
ax.set_xlabel("Revenue (BRL)")
plt.tight_layout()
plt.savefig(OUT_DIR / "top_categories.png", dpi=150)
plt.close()

# 3. Top 10 states
states = run("""
SELECT c.customer_state AS state, SUM(oi.price) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1 ORDER BY revenue DESC LIMIT 10
""")
print("\n--- Top 10 states ---")
print(states.round(0).to_string(index=False))

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(states["state"], states["revenue"], color="#54A24B")
ax.set_title("Top 10 States by Revenue")
ax.set_ylabel("Revenue (BRL)")
plt.tight_layout()
plt.savefig(OUT_DIR / "top_states.png", dpi=150)
plt.close()

# 4. Delivery delay vs review score
delay = run("""
SELECT CASE
         WHEN o.delay_days <= 0 THEN '1. On time / early'
         WHEN o.delay_days <= 7 THEN '2. Late 1-7 days'
         ELSE '3. Late 8+ days'
       END AS delivery_bucket,
       COUNT(*) AS orders,
       AVG(r.review_score) AS avg_review_score
FROM orders o
JOIN reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered' AND o.delay_days IS NOT NULL
GROUP BY 1 ORDER BY 1
""")
print("\n--- Delivery delay vs review score ---")
print(delay.round(2).to_string(index=False))

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(delay["delivery_bucket"], delay["avg_review_score"], color=["#54A24B", "#EECA3B", "#E45756"])
ax.set_ylim(0, 5)
ax.set_title("Average Review Score by Delivery Timeliness")
ax.set_ylabel("Avg review score (1-5)")
for b, v in zip(bars, delay["avg_review_score"]):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f"{v:.2f}", ha="center")
plt.tight_layout()
plt.savefig(OUT_DIR / "delay_vs_review.png", dpi=150)
plt.close()

print("\nSaved 4 charts in outputs/")