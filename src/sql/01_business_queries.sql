-- =====================================================
-- E-Commerce Intelligence & Customer Analytics Platform
-- Business queries on Olist dataset (PostgreSQL)
-- Note: revenue = sum of item price (freight excluded), delivered orders only
-- =====================================================


-- Q1: Overall KPIs
SELECT
  COUNT(DISTINCT o.order_id) AS total_orders,
  COUNT(DISTINCT c.customer_unique_id) AS unique_customers,
  ROUND(SUM(oi.price)::numeric, 2) AS revenue,
  ROUND((SUM(oi.price) / COUNT(DISTINCT o.order_id))::numeric, 2) AS avg_order_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_status = 'delivered';


-- Q2: Monthly revenue and month-over-month growth (window function LAG)
WITH monthly AS (
  SELECT DATE_TRUNC('month', o.order_purchase_timestamp) AS month,
         SUM(oi.price) AS revenue
  FROM orders o
  JOIN order_items oi ON o.order_id = oi.order_id
  WHERE o.order_status = 'delivered'
  GROUP BY 1
)
SELECT TO_CHAR(month, 'YYYY-MM') AS month,
       ROUND(revenue::numeric, 2) AS revenue,
       ROUND(((revenue - LAG(revenue) OVER (ORDER BY month))
              / LAG(revenue) OVER (ORDER BY month) * 100)::numeric, 1) AS mom_growth_pct
FROM monthly
ORDER BY month;


-- Q3: Top 10 product categories by revenue with revenue share
SELECT p.product_category_name_english AS category,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.price)::numeric, 2) AS revenue,
       ROUND((100 * SUM(oi.price) / SUM(SUM(oi.price)) OVER ())::numeric, 1) AS revenue_share_pct
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY revenue DESC
LIMIT 10;


-- Q4: Top 10 states by revenue
SELECT c.customer_state,
       COUNT(DISTINCT o.order_id) AS orders,
       ROUND(SUM(oi.price)::numeric, 2) AS revenue
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1
ORDER BY revenue DESC
LIMIT 10;


-- Q5: Payment method analysis
SELECT payment_type,
       COUNT(DISTINCT order_id) AS orders,
       ROUND(SUM(payment_value)::numeric, 2) AS total_value,
       ROUND(AVG(payment_installments)::numeric, 1) AS avg_installments
FROM payments
GROUP BY 1
ORDER BY orders DESC;


-- Q6: Impact of delivery delay on review score
SELECT
  CASE
    WHEN o.delay_days <= 0 THEN '1. On time / early'
    WHEN o.delay_days <= 7 THEN '2. Late 1-7 days'
    ELSE '3. Late 8+ days'
  END AS delivery_bucket,
  COUNT(*) AS orders,
  ROUND(AVG(r.review_score)::numeric, 2) AS avg_review_score
FROM orders o
JOIN reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered' AND o.delay_days IS NOT NULL
GROUP BY 1
ORDER BY 1;


-- Q7: Top 10 sellers by revenue with average review
SELECT oi.seller_id, s.seller_state,
       COUNT(DISTINCT oi.order_id) AS orders,
       ROUND(SUM(oi.price)::numeric, 2) AS revenue,
       ROUND(AVG(r.review_score)::numeric, 2) AS avg_review
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN sellers s ON oi.seller_id = s.seller_id
LEFT JOIN reviews r ON o.order_id = r.order_id
WHERE o.order_status = 'delivered'
GROUP BY 1, 2
ORDER BY revenue DESC
LIMIT 10;