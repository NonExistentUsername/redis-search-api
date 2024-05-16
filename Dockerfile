FROM nvidia/cuda:12.4.1-base-ubuntu22.04 as base

RUN apt-get update && \
    apt-get install -y python3-pip python3-dev python-is-python3 && \
    rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

FROM base as builder

COPY pyproject.toml ./
COPY redis_search_api ./redis_search_api

RUN touch README.md \
    && pip install "poetry==1.8.2" --no-cache-dir \
    && poetry config virtualenvs.create false \
    && poetry build -f wheel

FROM base as final

COPY --from=builder /app/dist/*.whl ./

RUN pip install ./*.whl --no-cache-dir \
    && rm -rf /app/*.whl

RUN sudo apt-get update && sudo apt-get upgrade -y && sudo apt-get install nvidia-driver-550 -y && sudo apt-get install nvidia-cuda-toolkit -y

CMD ["gunicorn", "--bind", "0.0.0.0:80",  "--workers", "1", "--threads", "4", "-k", "uvicorn.workers.UvicornWorker", "--timeout", "120", "redis_search_api.main:app"]