"""Northwind RDS PostgreSQL 接続モジュール"""

import os
import contextlib
import psycopg2
import psycopg2.extras
import streamlit as st


def get_connection_params() -> dict:
    """環境変数から DB 接続パラメータを取得する。"""
    return {
        "host": os.environ.get("RDS_HOST", "localhost"),
        "port": int(os.environ.get("RDS_PORT", "5432")),
        "dbname": os.environ.get("RDS_DBNAME", "northwind"),
        "user": os.environ.get("RDS_USER", "postgres"),
        "password": os.environ.get("RDS_PASSWORD", "postgres"),
    }


@st.cache_resource
def get_pool():
    """シンプルな接続プール (Streamlit キャッシュで再利用)。"""
    params = get_connection_params()
    return params


@contextlib.contextmanager
def get_cursor(dict_cursor=True):
    """DB カーソルのコンテキストマネージャ。自動 commit/rollback。"""
    params = get_pool()
    conn = psycopg2.connect(**params)
    try:
        cursor_factory = psycopg2.extras.RealDictCursor if dict_cursor else None
        with conn.cursor(cursor_factory=cursor_factory) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(query: str, params=None) -> list[dict]:
    """SELECT 結果を dict のリストで返す。"""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def fetch_one(query: str, params=None) -> dict | None:
    """SELECT 結果を 1 行だけ返す。"""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def execute(query: str, params=None) -> int:
    """INSERT/UPDATE/DELETE を実行し、影響行数を返す。"""
    with get_cursor(dict_cursor=False) as cur:
        cur.execute(query, params)
        return cur.rowcount


def execute_returning(query: str, params=None) -> dict | None:
    """INSERT ... RETURNING を実行し、結果行を返す。"""
    with get_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()
