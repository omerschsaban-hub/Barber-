FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PORT=8000
CMD ["sh","-c","exec uvicorn app.composed:app --host 0.0.0.0 --port ${PORT} --workers 2"]
