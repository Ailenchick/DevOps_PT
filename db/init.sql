DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END $$;

CREATE DATABASE $DB_DATABASE;


CREATE USER $DB_REPL_USER WITH REPLICATION ENCRYPTED PASSWORD '$DB_REPL_PASSWORD';
SELECT pg_create_physical_replication_slot('replication_slot');

GRANT ALL PRIVILEGES ON DATABASE $DB_DATABASE TO $DB_USER;

\connect $DB_DATABASE;

CREATE TABLE hba ( lines text ); 
COPY hba FROM '/var/lib/postgresql/data/pg_hba.conf'; 
INSERT INTO hba (lines) VALUES ('host replication $DB_REPL_USER 0.0.0.0/0 scram-sha-256'); 
INSERT INTO hba (lines) VALUES ('host all all 0.0.0.0/0 password'); 
COPY hba TO '/var/lib/postgresql/data/pg_hba.conf'; 
SELECT pg_reload_conf();


CREATE TABLE Phones (
    customerid SERIAL PRIMARY KEY,
    numberphone VARCHAR(20) NOT NULL
);

CREATE TABLE Emails (
    customerid SERIAL PRIMARY KEY,
    email VARCHAR(100) NOT NULL
);

INSERT INTO Emails (email) VALUES ('anton@kpnn.ru'), ('Vova@kpnn.com');

INSERT INTO Phones (numberphone) VALUES ('+7(123)4567890'), ('8-012-345-67-99');
