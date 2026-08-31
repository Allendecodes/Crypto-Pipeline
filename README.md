# Crypto Price Data Pipeline

An automated data pipeline that fetches live cryptocurrency prices from a public API, cleans and validates the data, stores it persistently in a SQL database, and runs on a daily schedule with no manual intervention — using GitHub Actions.

## Why I built this

Most beginner AI/ML portfolios show only the modeling side of the pipeline — a notebook trained on a static Kaggle CSV. In real AI/DS roles, a large part of the work is getting live, messy, ever-changing data into a usable form *before* any model ever sees it. This project demonstrates that other half: API integration, data cleaning, persistent storage, error handling, and automation — the full lifecycle a production data system actually needs.

## Tech stack

- **Python** — core language
- **requests** — API calls
- **pandas** — data cleaning and transformation
- **SQLite** — persistent structured storage
- **GitHub Actions** — daily automation (cron-based scheduling)

## How it works

1. **Fetch** — calls the [CoinGecko API](https://www.coingecko.com/en/api) to get live price, market cap, 24h volume, and 24h change for Bitcoin, Ethereum, and Solana.
2. **Clean** — the API returns nested JSON; this step flattens it into a structured table with pandas, converts Unix timestamps into readable dates, and safely handles any missing fields.
3. **Store** — cleaned rows are inserted into a SQLite database (`crypto_data.db`), using a composite primary key of `(coin, last_updated)` so the same price update is never stored twice, while genuinely new price data is always added.
4. **Automate** — a GitHub Actions workflow (`.github/workflows/daily_fetch.yml`) runs this entire pipeline once a day on a fresh virtual machine, then commits the updated database back to the repository so history accumulates over time.

## Key design decisions

**Why SQLite instead of a hosted database?**
SQLite requires no server setup and stores the entire database as a single file, making it ideal for a portfolio-scale project. In a production system with concurrent writers or larger scale, I'd move this to a hosted database like PostgreSQL — noted below as a future improvement.

**Why `(coin, last_updated)` as the primary key, not just `coin`?**
Prices update continuously. Using just `coin` as the key would mean only ever storing one row per coin, overwriting history. Using the combination of coin *and* its last-updated timestamp means every genuinely new price point gets stored, while running the script twice in quick succession (before the price has changed) won't create duplicate rows — `INSERT OR IGNORE` silently skips those.

**Why does the GitHub Actions workflow commit the database file back to the repo?**
Every GitHub Actions run starts from a completely fresh, empty environment — nothing persists between runs by default. Without committing the updated `.db` file back after each run, the pipeline would silently reset to zero every single day instead of building a real price history. This was a real bug I had to diagnose and fix during development (see below).

## Error handling

The pipeline is built to fail gracefully rather than crash silently:
- API requests have a timeout and are wrapped in exception handling — if CoinGecko is unreachable or returns a bad status, the script logs a clear message and exits cleanly instead of throwing an unhandled error.
- Each coin's data is processed individually inside its own try/except — if one coin has malformed data, it's skipped while the rest are still processed.
- Database operations are wrapped with a `finally` block to guarantee the connection is always closed properly, even if an error occurs mid-write.

## A real bug I hit (and why it happened)

During setup, the GitHub Actions run failed with `No such file or directory` even though the script ran fine locally. The cause: my local file was named `Fetch_prices.py` (capital F), but the workflow called `python fetch_prices.py` (lowercase). This worked on my Mac because macOS filesystems are case-insensitive — but GitHub Actions runs on Ubuntu Linux, where filenames **are** case-sensitive, so the two names pointed to genuinely different (and in this case, non-existent) files. This is a good example of a class of bug that only appears when moving from local development to a Linux-based deployment environment.

## How to run it locally

```bash
git clone https://github.com/Allendecodes/Crypto-Pipeline.git
cd Crypto-Pipeline
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install requests pandas
python fetch_prices.py
```

This will fetch the latest prices and append them to `crypto_data.db`.

## What I'd improve with more time

- Move from SQLite to a hosted database (PostgreSQL) for concurrent access and real production scale
- Add more coins and configurable coin lists instead of a hardcoded list
- Add alerting (e.g., an email or Slack message) if the daily pipeline run fails
- Add a lightweight dashboard (Streamlit) to visualize price trends over time directly from the stored data
- Add automated tests for the cleaning and insertion logic

## What this project demonstrates

- Working with real, live external APIs (authentication-free, rate-limited)
- Data cleaning and validation with pandas
- Relational database design fundamentals (schema design, primary keys, parameterized queries to prevent SQL injection)
- Production-minded error handling
- CI/CD-style automation with GitHub Actions, including diagnosing and fixing a real cross-platform deployment bug
