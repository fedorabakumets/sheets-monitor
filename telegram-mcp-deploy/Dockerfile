FROM python:3.13-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0

RUN apk add --no-cache git \
    && git clone --depth 1 https://github.com/chigwell/telegram-mcp.git /tmp/src \
    && cp -a /tmp/src/. /app \
    && rm -rf /tmp/src \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

CMD ["python", "main.py"]
