import os

import psycopg2
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash


load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


def main():
    database_url = os.getenv("DATABASE_URL")
    username = os.getenv("DEV_ADMIN_USERNAME")
    password = os.getenv("DEV_ADMIN_PASSWORD")

    if not database_url:
        raise SystemExit("DATABASE_URL is required.")

    if not username or not password:
        raise SystemExit("Set DEV_ADMIN_USERNAME and DEV_ADMIN_PASSWORD before running this script.")

    password_hash = generate_password_hash(password)

    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO system_users (username, password_hash, is_active)
                VALUES (%s, %s, TRUE)
                ON CONFLICT (username)
                DO UPDATE SET
                    password_hash = EXCLUDED.password_hash,
                    is_active = TRUE
                """,
                (username, password_hash),
            )

    print(f"Dev admin ready: {username}")


if __name__ == "__main__":
    main()
