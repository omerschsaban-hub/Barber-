FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY services/mcp/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY services/mcp/server.py ./server.py
COPY services/mcp/auth_server.py ./auth_server.py

EXPOSE 8000
ENV PORT=8000
CMD ["sh", "-c", "exec uvicorn auth_server:app --host 0.0.0.0 --port ${PORT}"]
