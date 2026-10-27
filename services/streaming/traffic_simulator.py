from __future__ import annotations

import asyncio
import json
import random
from datetime import datetime, timezone
import redis.asyncio as redis


async def main(redis_url: str = "redis://localhost:6379/0") -> None:
    client = redis.from_url(redis_url, decode_responses=True)
    segments = ["murree-road", "islamabad-expressway", "7th-avenue", "jinnah-avenue"]
    while True:
        event = {
            "type": "segment_observation",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "segments": [
                {
                    "segment_id": segment,
                    "avg_speed_kph": round(random.uniform(18, 62), 1),
                    "congestion_index": round(random.uniform(0.12, 0.88), 3),
                    "sample_count": random.randint(4, 90),
                }
                for segment in segments
            ],
        }
        await client.publish("traffic.events", json.dumps(event))
        await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())

