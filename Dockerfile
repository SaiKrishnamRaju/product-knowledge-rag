FROM python:3.12-slim
WORKDIR /code
RUN pip install --no-cache-dir uv
COPY requirements.txt ./
RUN uv pip install --system --no-cache torch --index-url https://download.pytorch.org/whl/cpu \
    && uv pip install --system --no-cache -r requirements.txt
COPY app ./app
COPY web ./web
COPY scripts/check_model_memory.py ./scripts/check_model_memory.py
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
