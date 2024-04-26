import hmac
import time
from typing import Union

from fastapi import FastAPI, HTTPException

from redis_search_api.constants import ACCESS_TOKEN
from redis_search_api.db import search as redis_search

app = FastAPI()


@app.get("/search/")
async def search(token: str, query: str, results_count: int):
    if hmac.compare_digest(token, ACCESS_TOKEN) is False:
        return HTTPException(status_code=401, detail="Invalid token")

    if results_count < 1:
        return HTTPException(
            status_code=400, detail="Results count should be greater than 0"
        )

    if not query:
        return HTTPException(status_code=400, detail="Query should not be empty")

    if results_count > 100:
        return HTTPException(
            status_code=400, detail="Results count should be less than or equal to 100"
        )

    if len(query) > 100000:
        return HTTPException(
            status_code=400,
            detail="Query should be less than or equal to 100000 characters",
        )

    start = time.time()
    docs = await redis_search(query, k=25000, results_count=results_count)
    end = time.time()

    results = [
        {
            "url": getattr(doc, "url", "N/A"),
            "score": getattr(doc, "vector_score", "N/A"),
        }
        for doc in docs
    ]
    return {
        "results": results,
        "search_time": end - start,
        "count": len(results),
    }
