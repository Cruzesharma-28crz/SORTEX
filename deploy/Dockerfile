FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 SORTEX_PORTAL_DIR=/app/portal
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir ".[server]"
EXPOSE 8000
CMD ["uvicorn", "sortex_cloud.main:app", "--host", "0.0.0.0", "--port", "8000"]
