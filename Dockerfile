FROM python:3.11.4-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    CUDA_VISIBLE_DEVICES=-1

WORKDIR /app

FROM base as builder

COPY pyproject.toml ./
COPY redis_search_api ./redis_search_api

RUN touch README.md \
    && pip install "poetry==1.6.1" --no-cache-dir \
    && poetry config virtualenvs.create false \
    && poetry build -f wheel

FROM base as final

COPY --from=builder /app/dist/*.whl ./

RUN pip install ./*.whl --no-cache-dir \
    && rm -rf /app/*.whl

CMD ["gunicorn", "--bind", "0.0.0.0:80",  "--workers", "1", "--threads", "4", "-k", "--timeout", "120", "uvicorn.workers.UvicornWorker", "redis_search_api.main:app"]