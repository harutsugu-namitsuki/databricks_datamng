"""DB接続 (FastAPI 用)"""

import os
import contextlib
import psycopg2
import psycopg2.extras


def _params():
    return {
        "host": os.environ.get("RDS_HOST", "localhost"),
        "port": int(os.environ.get("RDS_PORT", "5432")),
        "dbname": os.environ.get("RDS_DBNAME", "northwind"),
        "user": os.environ.get("RDS_USER", "postgres"),
        "password": os.environ.get("RDS_PASSWORD", "postgres"),
    }


@contextlib.contextmanager
def _cursor(dict_cursor=True):
    conn = psycopg2.connect(**_params())
    try:
        factory = psycopg2.extras.RealDictCursor if dict_cursor else None
        with conn.cursor(cursor_factory=factory) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query, params=None):
    with _cursor() as cur:
        cur.execute(query, params)
        return [dict(r) for r in cur.fetchall()]


def fetch_one(query, params=None):
    with _cursor() as cur:
        cur.execute(query, params)
        row = cur.fetchone()
        return dict(row) if row else None


def execute(query, params=None):
    with _cursor(dict_cursor=False) as cur:
        cur.execute(query, params)
        return cur.rowcount
