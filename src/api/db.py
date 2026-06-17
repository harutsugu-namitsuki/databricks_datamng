"""DB接続 (FastAPI 用)"""

import os
import time
import contextlib
from pathlib import Path

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from api import trace

# リポジトリ直下の .env を読み込む（src/api/db.py → parents[2] = リポジトリルート）。
# これが無いと os.environ に接続情報が入らず、既定値(localhost/postgres)に落ちる。
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


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
    t0 = time.perf_counter()
    status = "ok"
    try:
        with _cursor() as cur:
            cur.execute(query, params)
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        status = "error"
        raise
    finally:
        _record_sql(query, params, (time.perf_counter() - t0) * 1000, status)


def fetch_one(query, params=None):
    t0 = time.perf_counter()
    status = "ok"
    try:
        with _cursor() as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception:
        status = "error"
        raise
    finally:
        _record_sql(query, params, (time.perf_counter() - t0) * 1000, status)


def execute(query, params=None):
    t0 = time.perf_counter()
    status = "ok"
    try:
        with _cursor(dict_cursor=False) as cur:
            cur.execute(query, params)
            return cur.rowcount
    except Exception:
        status = "error"
        raise
    finally:
        _record_sql(query, params, (time.perf_counter() - t0) * 1000, status)


def _record_sql(query, params, dur_ms, status):
    """SQL span を記録。トレース失敗は握りつぶす（FR-T6）。"""
    try:
        trace.record(trace.make_span(
            "db", "db.py", "sql",
            detail=" ".join(str(query).split()),  # 改行を畳む
            tables=trace.extract_tables(str(query)),
            dur_ms=dur_ms,
            status=status,
        ))
    except Exception:
        pass
