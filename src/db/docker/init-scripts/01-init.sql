-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema
CREATE SCHEMA IF NOT EXISTS instructor_schema;

-- Set search path
SET search_path TO instructor_schema, public;

-- Create role for application
DO
$$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN
    CREATE ROLE app_user WITH LOGIN PASSWORD 'app_password';
  END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON SCHEMA instructor_schema TO app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA instructor_schema TO app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA instructor_schema TO app_user;

-- Create test database for testing
CREATE DATABASE instructor_test_db WITH OWNER postgres;
