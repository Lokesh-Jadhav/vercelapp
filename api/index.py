from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import os
import numpy as np

app = FastAPI()

# Enable CORS for all origins (POST + OPTIONS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load JSON telemetry data (file is one level up from /api)
json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../q-vercel-latency.json"))

with open(json_path, "r") as f:
    telemetry_data = json.load(f)

@app.get("/")
def home():
    return {"message": "Latency API running"}

@app.post("/api/latency")   # ✅ endpoint is /api/latency
async def latency(request: Request):
    body = await request.json()
    regions: List[str] = body.get("regions", [])
    threshold_ms: int = body.get("threshold_ms", 0)

    response = {}

    for region in regions:
        # ✅ fixed bug: use telemetry_data, not latency_data
        region_data = [r for r in telemetry_data if r["region"] == region]
        if not region_data:
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]

        response[region] = {
            "avg_latency": round(float(np.mean(latencies)), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(np.mean(uptimes)), 3),
            "breaches": sum(1 for l in latencies if l > threshold_ms)
        }

    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.index:app", host="0.0.0.0", port=5000, reload=True)
