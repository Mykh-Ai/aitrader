FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir websocket-client requests

COPY binance_aggregator_shi.py .

CMD ["python", "-u", "binance_aggregator_shi.py"]
