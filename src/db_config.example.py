from sqlalchemy.engine import URL

DB_URL = URL.create(
    "postgresql+psycopg2",
    username="postgres",
    password="Your Password",
    host="localhost",
    port=5432,
    database="olist",
)