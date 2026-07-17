FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 9090

CMD ["streamlit", "run", "app.py", \
    "--server.address=0.0.0.0", \
    "--server.port=9090", \
    "--server.runOnSave=true", \
    "--server.fileWatcherType=poll"]