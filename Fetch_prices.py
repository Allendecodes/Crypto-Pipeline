import requests

url = "https://api.coingecko.com/api/v3/simple/price"
params = {
    "ids": "bitcoin,ethereum,solana",
    "vs_currencies": "usd",
    "include_market_cap": "true",
    "include_24hr_vol": "true",
    "include_24hr_change": "true",
    "include_last_updated_at": "true"
}

response = requests.get(url, params=params)
print(response.status_code) #it tells you 200 if the request was successful
print(response.json()) # converts the reply into a Python dictionary

#API responses come back as nested key-value data ({"bitcoin": {"usd": 79618, ...}})

from datetime import datetime
import pandas as pd
data = response.json()
#Data cleaning with pandas
rows = []
for coin, values in data.items(): 
    rows.append({
        "coin": coin,
        "price_usd": values.get("usd"),
        "market_cap_usd": values.get("usd_market_cap"),
        "volume_24h_usd": values.get("usd_24h_vol"),
        "change_24h_pct": values.get("usd_24h_change"),
        "last_updated": datetime.fromtimestamp(values.get("last_updated_at")),
        "fetched_at": datetime.now()
    })

import sqlite3
conn = sqlite3.connect("crypto_data.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS prices (
        coin TEXT,
        price_usd REAL,
        market_cap_usd REAL,
        volume_24h_usd REAL,
        change_24h_pct REAL,
        last_updated TEXT,
        fetched_at TEXT,
        PRIMARY KEY (coin, last_updated)
    )
""")

for row in rows:
    cursor.execute("""
        INSERT OR IGNORE INTO prices
        (coin, price_usd, market_cap_usd, volume_24h_usd, change_24h_pct, last_updated, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        row["coin"],
        row["price_usd"],
        row["market_cap_usd"],
        row["volume_24h_usd"],
        row["change_24h_pct"],
        str(row["last_updated"]),
        str(row["fetched_at"])
    ))

conn.commit()

conn.commit()
check_df = pd.read_sql("SELECT * FROM prices", conn)
print(check_df)
conn.close()

print("Data saved to crypto_data.db")