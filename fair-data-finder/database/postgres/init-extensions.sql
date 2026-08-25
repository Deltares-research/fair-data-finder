-- PostgreSQL extensions
-- Runs once when the data directory is created
--
-- Required by PostGIS + pgstac.  The pypgstac migrate command expects all four
-- extensions to exist in the target database before it installs the pgstac schema.


CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE EXTENSION IF NOT EXISTS unaccent;
