FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p memory bots logs
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=10000
EXPOSE 10000
CMD ["sh", "-c", "python gateway/slack_bot.py"]
