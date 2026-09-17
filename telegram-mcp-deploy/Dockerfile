FROM python:3.13-alpine

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MCP_TRANSPORT=http
ENV MCP_HOST=0.0.0.0

COPY delete_topics.py /delete_topics.py

RUN apk add --no-cache git \
    && git clone --depth 1 https://github.com/chigwell/telegram-mcp.git /tmp/src \
    && cp -a /tmp/src/. /app \
    && rm -rf /tmp/src \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app /delete_topics.py

USER appuser

CMD ["python", "main.py"]
