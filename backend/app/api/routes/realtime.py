import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect


router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.websocket("/traffic")
async def traffic_socket(ws: WebSocket) -> None:
    await ws.accept()
    tick = 0
    try:
        while True:
            tick += 1
            await ws.send_text(
                json.dumps(
                    {
                        "type": "traffic_update",
                        "tick": tick,
                        "segments": [
                            {"segment_id": "isl-7th-ave", "congestion": min(0.95, 0.35 + tick % 10 / 30)},
                            {"segment_id": "murree-road", "congestion": min(0.9, 0.45 + tick % 8 / 25)},
                        ],
                    }
                )
            )
            await asyncio.sleep(4)
    except WebSocketDisconnect:
        return

