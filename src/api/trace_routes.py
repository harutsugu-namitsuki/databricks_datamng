"""可視化ビュー向け API: 経路マップ・リアルタイム配信(SSE)・履歴集計。"""

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from api import trace

router = APIRouter(prefix="/trace", tags=["trace"])
_MAP = json.loads((Path(__file__).resolve().parent / "trace_map.json").read_text(encoding="utf-8"))


@router.get("/map")
def get_map():
    return JSONResponse(_MAP)


@router.get("/stream")
async def stream(request: Request):
    """Server-Sent Events。新規 span を逐次 push（3秒以内: FR-R1）。"""
    q = trace.subscribe()

    async def gen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    span = await asyncio.wait_for(q.get(), timeout=15)
                    yield f"data: {json.dumps(span, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            trace.unsubscribe(q)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.get("/rollup")
def rollup(window: str = "1h"):
    """指定時間窓のエッジ別通過量を返す（進行中バケットも途中経過として含む: FR-S2）。"""
    return JSONResponse(trace.rollup_for(window))
