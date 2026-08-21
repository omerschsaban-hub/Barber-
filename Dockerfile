FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY engineering/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY engineering/app ./app

EXPOSE 8000

CMD ["uvicorn", "app.composed:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
