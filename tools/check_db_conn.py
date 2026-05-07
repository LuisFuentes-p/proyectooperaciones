import psycopg

candidates = [
    "postgresql://user:password@localhost:5432/transactions_db",
    "postgresql://postgres:postgres@localhost:5432/transactions_db",
    "postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/transactions_db",
    "postgresql://user:password@127.0.0.1:5432/transactions_db",
]

for url in candidates:
    try:
        with psycopg.connect(url) as conn:
            with conn.cursor() as cur:
                cur.execute("select current_user, current_database()")
                row = cur.fetchone()
        print("OK", url, row)
    except Exception as e:
        print("FAIL", url, str(e).splitlines()[0])
