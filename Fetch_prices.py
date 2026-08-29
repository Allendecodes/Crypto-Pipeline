import requests #for making HTTP requests to the API
import sqlite3

url = "https://api.coingecko.com/api/v3/simple/price"#the API endpoint for fetching cryptocurrency prices
params = {#these are the parameters you are getting from the API
    "vs_currencies": "usd",
    "ids": "bitcoin,ethereum,solana",#these are the parameters you are getting from the API,
    "include_market_cap": "true",
    "include_24hr_vol": "true",
    "include_24hr_change": "true",
    "include_last_updated_at": "true"
}
#next for error handling here
try:
    response = requests.get(url, params=params,timeout = 10)
    response.raise_for_status()  # Raise an error for HTTP errors
except requests.RequestException as e:
    print(f"Error fetching API data: {e}")
    exit(1)  # stop the script cleanly, don't proceed with broken data

print(response.status_code) #it tells you 200 if the request was successful
print(response.json()) # converts the reply into a Python dictionary


from datetime import datetime
import pandas as pd
data = response.json()#The API's response is nested ({"bitcoin": {"usd": ..., "usd_market_cap": ...}}), which is hard to work with directly.

rows = []
for coin, values in data.items(): #This loop goes through each coin, pulls out its values using .get()
    try:
        rows.append({
            "coin": coin,
            "price_usd": values.get("usd"),
            "market_cap_usd": values.get("usd_market_cap"),
            "volume_24h_usd": values.get("usd_24h_vol"),
            "change_24h_pct": values.get("usd_24h_change"),
            "last_updated": datetime.fromtimestamp(values.get("last_updated_at")),#datetime.fromtimestamp() converts the API's raw timestamp into a human-readable date.
            "fetched_at": datetime.now()
            })
    except (TypeError, ValueError) as e:
        print(f"Skipping {coin} due to bad data: {e}")
        continue  # skip this coin, keep processing the rest

if not rows:
    print("No valid data to save. Exiting.")
    exit(1)

df = pd.DataFrame(rows)

try:
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
    print(f"Data saved to crypto_data.db ({len(rows)} coins processed)")

except sqlite3.Error as e:
    print(f"Database error: {e}")
finally:
    conn.close()