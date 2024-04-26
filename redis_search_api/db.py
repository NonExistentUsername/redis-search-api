from typing import Dict, List, Union

import redis.asyncio as redis
from redis.commands.search.query import Query

from redis_search_api.constants import REDIS_DB, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from redis_search_api.embeddings import get_embeddings

INDEX_NAME = "idx:pages_vss"


def get_redis_client():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
    )


async def search(query: str, k: int = 10, results_count: int = 10):
    client = get_redis_client()
    query_obj = (
        Query(f"(*)=>[KNN {k} @embeddings $query_vector AS vector_score]")
        .return_fields("url", "vector_score")
        .sort_by("vector_score", asc=True)
        .paging(0, results_count)
        .dialect(2)
    )
    results = await client.ft(INDEX_NAME).search(
        query_obj,
        {
            "query_vector": get_embeddings(query),
        },
    )

    await client.aclose()
    return results.docs
