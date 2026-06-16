#!/bin/bash
# FastAPI + HTML/JS アプリを起動する

# .env を読み込む
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# src ディレクトリから起動 (api モジュールのパス解決のため)
cd src
uvicorn api.main:app --reload --port 8000
