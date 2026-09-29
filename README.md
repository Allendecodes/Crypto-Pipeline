# CryptoPulse —  Cryptocurrency Analytics Platform

CryptoPulse is an end-to-end cryptocurrency data platform that automatically collects market data from the CoinGecko API, transforms and validates the response, stores historical observations in SQLite, exposes the data through a Flask REST API, and visualizes it through an interactive web dashboard.

The project combines **data engineering, backend development, database design, frontend development, and workflow automation** in one application.

## Architecture

```
                         CoinGecko API
                              │
                              ▼
                    Python Data Pipeline
                    Requests + Pandas
                              │
                       Cleaned data
                              │
                              ▼
                    SQLite: crypto_data.db
                              │
                         SQL queries
                              │
                              ▼
                    Flask REST API
                    /api/latest
                    /api/prices
                              │
                            JSON
                              │
                              ▼
                  HTML + CSS + JavaScript
                         + Chart.js
                              │
                              ▼
                    CryptoPulse Dashboard

                    GitHub Actions
                         │
                         └── Scheduled ingestion
                             every 5 minutes
```

## What the application does

1. **Fetches** cryptocurrency market data for Bitcoin, Ethereum, and Solana from CoinGecko.
2. **Transforms** nested JSON responses into structured records using Python and Pandas.
3. **Validates and timestamps** the incoming records.
4. **Stores** historical observations in SQLite.
5. **Exposes** stored data through Flask REST endpoints.
6. **Visualizes** current and historical market information in a browser dashboard.
7. **Automates** data ingestion using GitHub Actions.

## Dashboard

The CryptoPulse dashboard displays:

- Current BTC, ETH, and SOL prices
- 24-hour percentage changes
- Market capitalization
- 24-hour trading volume
- Historical price trends
- Automatic dashboard refresh
- Latest data timestamp

The dashboard is periodically refreshed rather than being a tick-by-tick trading feed. The ingestion workflow runs every 5 minutes.

## Tech Stack

| Layer | Technology |
|---|---|
| External data | CoinGecko API |
| Data ingestion | Python, Requests |
| Data processing | Pandas |
| Database | SQLite |
| Backend | Flask |
| API format | REST / JSON |
| Frontend | HTML, CSS, JavaScript |
| Visualization | Chart.js |
| Automation | GitHub Actions |
| Production server configuration | Gunicorn |

## Backend API

### Get latest prices

```
GET /api/latest
```

Returns the latest stored observation for each cryptocurrency.

Example:

```json
[
  {
    "coin": "bitcoin",
    "price_usd": 82787,
    "change_24h_pct": -2.24
  }
]
```

### Get historical prices

```
GET /api/prices
```

Returns stored historical records used to build the price-history chart.

## Data Model

The SQLite database contains a `prices` table with fields including:

```
coin
price_usd
market_cap_usd
volume_24h_usd
change_24h_pct
last_updated
fetched_at
```

The design uses **(coin, last_updated)** as the composite primary key.

This allows the database to retain historical observations:

```
bitcoin | 10:00 | $82,000
bitcoin | 10:05 | $82,100
bitcoin | 10:10 | $82,250
```

while preventing the same observation from being inserted repeatedly.

## End-to-End Data Flow

Suppose the dashboard displays:

```
BTC
$82,787
-2.24%
```

That value passes through the following flow:

```
1. CoinGecko provides the market data
             ↓
2. fetch_prices.py requests the API
             ↓
3. Python receives nested JSON
             ↓
4. Pandas transforms it into structured records
             ↓
5. SQLite stores the observation
             ↓
6. Flask queries SQLite
             ↓
7. /api/latest returns JSON
             ↓
8. JavaScript calls the endpoint
             ↓
9. The frontend updates the BTC card
             ↓
10. The user sees the value in CryptoPulse
```

The historical chart follows a similar path through `/api/prices`, after which Chart.js converts the returned timestamps and prices into a time-series visualization.

## Automation with GitHub Actions

The workflow is located at:

```
.github/workflows/daily_fetch.yml
```

It is scheduled to run every 5 minutes.

The workflow:

```
GitHub Actions
      ↓
Checkout repository
      ↓
Install dependencies
      ↓
Run fetch_prices.py
      ↓
Update crypto_data.db
      ↓
Commit updated database
```

The database is committed back to the repository because GitHub Actions runners are temporary. Without persistence outside the runner, the updated SQLite database would be lost after the workflow finished.

## Error Handling

The ingestion pipeline includes:

- Request timeouts
- HTTP error handling
- Exception handling around external API requests
- Per-coin processing so one malformed record does not necessarily stop the complete batch
- Database cleanup using connection handling
- Duplicate prevention using the composite primary key

## Why These Technologies?

### Why Flask?

The application needs a lightweight backend with a small number of REST endpoints and database operations. Flask provides this without the overhead of a larger web framework.

### Why SQLite?

SQLite is serverless and stores the database in a single file, making it appropriate for a lightweight portfolio application. For a production system with higher concurrency and scale, PostgreSQL would be a better choice.

### Why Pandas?

The CoinGecko response is nested JSON. Pandas makes it convenient to transform the response into structured records before database insertion.

### Why a backend API?

The frontend does not directly access CoinGecko or the SQLite database. Flask provides a clean separation:

```
Frontend
   ↓
Flask REST API
   ↓
Database
```

This makes the application easier to extend and allows the data layer to remain independent of the presentation layer.

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/Allendecodes/Crypto-Pipeline.git
cd Crypto-Pipeline
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the Flask application

```bash
python app.py
```

By default, Flask runs on:

```
http://localhost:5000
```

If port 5000 is already in use, run the application on another port, for example:

```bash
python -c "from app import app; app.run(host='0.0.0.0', port=5001, debug=True)"
```

Then open:

```
http://localhost:5001
```

### 5. Run the ingestion pipeline manually

If new data needs to be collected manually:

```bash
python fetch_prices.py
```

Then refresh the dashboard.

## Project Structure

```
Crypto-Pipeline/
│
├── app.py                         # Flask backend and REST APIs
├── fetch_prices.py                # CoinGecko ingestion pipeline
├── crypto_data.db                 # SQLite database
├── requirements.txt               # Python dependencies
├── Procfile                       # Gunicorn start command
├── templates/
│   └── index.html                 # Dashboard frontend
├── .github/
│   └── workflows/
│       └── daily_fetch.yml        # Automated ingestion workflow
└── README.md
```

## Key Engineering Decisions

### Historical storage instead of overwriting

The system stores observations instead of keeping only the current price. This makes historical visualization possible.

### Composite primary key

`(coin, last_updated)` identifies an individual observation and prevents duplicate records.

### Separation of concerns

The project separates:

- Data ingestion
- Data transformation
- Data persistence
- Backend/API logic
- Frontend presentation
- Workflow automation

This makes each component easier to understand and modify independently.

## Future Improvements

For a production-oriented version, I would:

- Migrate SQLite to PostgreSQL
- Add database indexes optimized for time-series queries
- Add retry logic with exponential backoff for external API failures
- Add automated unit and integration tests
- Add API authentication/rate limiting where appropriate
- Add monitoring and alerting for failed pipeline runs
- Add WebSockets or Server-Sent Events for genuinely real-time updates
- Containerize the application using Docker
- Add configurable cryptocurrency selection instead of a fixed list
- Deploy the Flask application using a production WSGI server

## What This Project Demonstrates

- External REST API integration
- Python data ingestion
- JSON transformation and data cleaning
- Pandas data processing
- SQL and relational database fundamentals
- Composite keys and duplicate prevention
- Flask REST API development
- Frontend-to-backend communication
- JavaScript asynchronous API calls
- Data visualization with Chart.js
- Automated workflows with GitHub Actions
- Error handling and production-minded design decisions

## Project Demo

The application can be demonstrated locally through the Flask dashboard:

```
http://localhost:5001
```

The repository contains the complete source code and automation workflow.

---

**Built as an end-to-end cryptocurrency data engineering and full-stack analytics project.**
