import os
import logging

from psycopg2 import pool, OperationalError
from fastapi import HTTPException

from config_env import load_project_env

load_project_env()

DB_CONFIG = {
    "dbname": os.environ.get("DB_NAME", "lostfound"),
    "user": os.environ.get("DB_USER", "appuser"),
    "password": os.environ.get("DB_PASSWORD", "password"),
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "5432"),
}

# Create a global connection pool
try:
    connection_pool = pool.ThreadedConnectionPool(1, 20, **DB_CONFIG)
    if connection_pool:
        logging.info("Database connection pool created successfully")
except Exception as e:
    logging.error(f"Error creating connection pool: {e}")
    connection_pool = None

def get_db_connection():
    if not connection_pool:
        raise HTTPException(status_code=503, detail="数据库连接池未初始化")
    try:
        conn = connection_pool.getconn()
        return conn
    except OperationalError:
        raise HTTPException(status_code=503, detail="无法从连接池获取数据库连接")

def release_db_connection(conn):
    if connection_pool and conn:
        connection_pool.putconn(conn)
