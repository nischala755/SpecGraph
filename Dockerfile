FROM node:22-alpine AS frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/pyproject.toml ./
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" neo4j pydantic httpx rapidfuzz datasketch "sentence-transformers[onnx]"
COPY backend/app ./app
COPY seed ./seed
COPY --from=frontend /frontend/dist ./static
ENV PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000"]
