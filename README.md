# Lksfy Bypass Bot

A Telegram bot designed to bypass `lksfy.com` shortened links. It uses a hybrid approach combining fast HTTP requests with a headless browser (Playwright) to navigate redirect chains and solve Cloudflare Turnstile CAPTCHAs.

## Features

*   **Hybrid Bypass Engine:** Uses `requests` for speed on standard redirects and switches to `playwright` (Chromium) only when a CAPTCHA is detected.
*   **CAPTCHA Solver:** Automatically handles Cloudflare Turnstile challenges.
*   **Cookie Persistence:** Maintains session state across both engines to ensure successful navigation through long redirect chains.
*   **Dockerized:** Ready for deployment on platforms like Heroku using Docker containers.
*   **Formatted Output:** Returns the final destination link in a clean, structured message.

## Requirements

*   Python 3.12+
*   Playwright (and Chromium browser binary)
*   Docker (for deployment)

## Local Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <your-repo-folder>
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers:**
    ```bash
    playwright install chromium
    ```

4.  **Set Environment Variables:**
    Create a `.env` file or export the variable in your shell:
    ```bash
    export BOT_TOKEN="your_telegram_bot_token"
    ```

5.  **Run the bot:**
    ```bash
    python bot.py
    ```

## Deployment on Heroku (Docker)

This project uses `heroku.yml` and a `Dockerfile` because standard Buildpacks often struggle with Playwright dependencies.

1.  **Create a Heroku App:**
    ```bash
    heroku create your-app-name
    ```

2.  **Set the Stack to Container:**
    ```bash
    heroku stack:set container
    ```

3.  **Set Config Vars:**
    Go to your Heroku Dashboard -> Settings -> Config Vars, or use CLI:
    ```bash
    heroku config:set BOT_TOKEN="your_telegram_bot_token"
    ```

4.  **Push to Heroku:**
    ```bash
    git push heroku main
    ```

## Usage

1.  Start a chat with your bot.
2.  Send `/start` to verify it's running.
3.  Send any link containing `lksfy.com`.
4.  The bot will reply "Bypassing..." and may take a few minutes if multiple CAPTCHAs are encountered.
5.  Once finished, it will reply with the original and bypassed link.

## Disclaimer

This tool is for educational purposes only.
