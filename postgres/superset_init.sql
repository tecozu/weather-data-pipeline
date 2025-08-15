-- This file is used to initialize the PostgreSQL database for Superset

CREATE USER superset WITH PASSWORD 'superset';
CREATE DATABASE superset_db WITH OWNER superset;
CREATE USER examples WITH PASSWORD 'examples';
CREATE DATABASE examples_db WITH OWNER examples;