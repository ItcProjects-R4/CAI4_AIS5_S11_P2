DROP DATABASE IF EXISTS shoporder;

CREATE DATABASE shoporder ENCODING 'UTF8' LOCALE 'en_US.UTF-8';

-- Note: The following SQL files (02_create_staging_tables.sql, etc.)
-- should be run AFTER connecting to the shoporder database using:
-- psql -U postgres -d shoporder -f 02_create_staging_tables.sql