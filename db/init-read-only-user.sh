#!/bin/bash
set -e

# These variables should match the ones in your .env file
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create the user if it doesn't exist
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$POSTGRES_READONLY_USER') THEN
            CREATE ROLE $POSTGRES_READONLY_USER WITH LOGIN PASSWORD '$POSTGRES_READONLY_PASSWORD';
        END IF;
    END
    \$\$;

    -- Grant read-only permissions
    GRANT CONNECT ON DATABASE $POSTGRES_DB TO $POSTGRES_READONLY_USER;
    GRANT USAGE ON SCHEMA public TO $POSTGRES_READONLY_USER;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO $POSTGRES_READONLY_USER;
    
    -- Ensure future tables are also read-only for this user
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO $POSTGRES_READONLY_USER;
EOSQL