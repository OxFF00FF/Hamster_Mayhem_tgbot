FROM python:3.9-alpine

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

COPY .env requirements.txt ./

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

CMD ["python", "bot/main.py"]