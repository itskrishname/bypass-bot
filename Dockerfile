FROM python:3.12-slim

# Install system dependencies required for Playwright
# We install playwright first to get the browser binaries
# But playwright needs system libs.
# 'playwright install-deps' can do this, but in Docker we often need to be explicit or use the playwright image.
# Using the official playwright image is safer.

FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install chromium explicitly if needed, but the base image usually has it.
# We ensure it's installed.
RUN playwright install chromium

COPY . .

# Run the bot
CMD ["python", "bot.py"]
