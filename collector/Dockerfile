FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Seoul

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

RUN useradd --create-home --uid 10001 withbid \
    && mkdir -p /state \
    && chown -R withbid:withbid /app /state

USER withbid

CMD ["python", "scheduler.py"]
