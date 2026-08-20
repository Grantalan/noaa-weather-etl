FROM python:3.13-slim
WORKDIR /app
RUN mkdir -p data/raw data/processed
COPY . .
RUN pip install uv
RUN uv sync --frozen
CMD ["uv", "run", "python", "main.py"]
