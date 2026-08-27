FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY engineering/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY engineering ./engineering
COPY services ./services
COPY db ./db
ENV PYTHONPATH=/app

EXPOSE 8000
ENV PORT=8000

CMD ["sh","-c","exec uvicorn services.engine.main:app --host 0.0.0.0 --port ${PORT} --workers 2"]
