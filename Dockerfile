FROM python:3.12.13-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && \
    adduser \
        --disabled-password \
        --no-create-home \
        --gecos "" \
        django-user

COPY --chown=django-user:django-user . .

RUN mkdir -p /data && \
    chown -R django-user:django-user /app /data

USER django-user
