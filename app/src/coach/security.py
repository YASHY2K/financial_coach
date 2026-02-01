import logging
from sqlalchemy import create_engine, text

try:
    from coach.config import settings
except ImportError:
    from config import settings

logger = logging.getLogger("security")


def setup_readonly_user():
    """
    Ensures the read-only database user exists and has correct permissions.
    This is idempotent and safe to run on every startup.
    """
    try:
        # Connect as ADMIN (using the default async url but converting to sync for this operation)
        admin_db_url = settings.database_url.replace("+asyncpg", "+psycopg2")

        # Isolation level AUTOCOMMIT is required for CREATE USER / DATABASE commands
        engine = create_engine(admin_db_url, isolation_level="AUTOCOMMIT")

        readonly_user = settings.POSTGRES_READONLY_USER
        readonly_pass = settings.POSTGRES_READONLY_PASSWORD
        db_name = settings.POSTGRES_DB

        logger.info("Checking read-only database user permissions...")

        with engine.connect() as conn:
            # Create Role if it doesn't exist
            check_user_sql = text("SELECT 1 FROM pg_roles WHERE rolname=:name")
            result = conn.execute(check_user_sql, {"name": readonly_user}).fetchone()

            if not result:
                logger.info(f"Creating user '{readonly_user}'...")
                conn.execute(
                    text(f"CREATE USER {readonly_user} WITH PASSWORD '{readonly_pass}'")
                )
            else:
                # Optional: Update password to match config
                conn.execute(
                    text(f"ALTER USER {readonly_user} WITH PASSWORD '{readonly_pass}'")
                )

            # 3. Grant Permissions
            # These are idempotent (granting twice is fine)
            conn.execute(
                text(f"GRANT CONNECT ON DATABASE {db_name} TO {readonly_user}")
            )
            conn.execute(text(f"GRANT USAGE ON SCHEMA public TO {readonly_user}"))
            conn.execute(
                text(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {readonly_user}")
            )

            # 4. Ensure Future Tables are Readable
            conn.execute(
                text(
                    f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {readonly_user}"
                )
            )

            logger.info("Read-only user verification complete.")

    except Exception as e:
        logger.error(f"Failed to setup read-only user: {e}")
        # We don't raise here to avoid crashing the app if DB isn't ready,
        # though ideally the app should wait for DB.
