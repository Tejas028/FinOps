FROM python:3.11-slim

WORKDIR /app

# Copy shared schemas first (dependency of api/)
COPY shared/ ./shared/
COPY storage/ ./storage/
COPY api/ ./api/

RUN pip install --no-cache-dir -r api/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "api.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2"]
