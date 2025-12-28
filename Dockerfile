FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set Playwright Browsers Path
ENV PLAYWRIGHT_BROWSERS_PATH=/app/pw-browsers

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy app code
COPY . .

# Copy start script
COPY start.sh .
RUN chmod +x start.sh

# Run the bot
CMD ["./start.sh"]
