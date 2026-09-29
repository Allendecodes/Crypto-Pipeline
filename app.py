from flask import Flask, jsonify, render_template, request
import sqlite3
from pathlib import Path

app = Flask(__name__)
DB_PATH = Path(__file__).with_name("crypto_data.db")


def query_db(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


@app.get("/")
def dashboard():
    return render_template("index.html")


@app.get("/api/prices")
def prices():
    limit = min(max(request.args.get("limit", default=100, type=int), 1), 500)
    rows = query_db(
        """
        SELECT coin, price_usd, market_cap_usd, volume_24h_usd,
               change_24h_pct, last_updated, fetched_at
        FROM prices
        ORDER BY datetime(last_updated) DESC
        LIMIT ?
        """,
        (limit,),
    )
    return jsonify(rows)


@app.get("/api/latest")
def latest():
    rows = query_db(
        """
        SELECT p.*
        FROM prices p
        INNER JOIN (
            SELECT coin, MAX(datetime(last_updated)) AS latest_updated
            FROM prices
            GROUP BY coin
        ) latest
        ON p.coin = latest.coin
        AND datetime(p.last_updated) = latest.latest_updated
        ORDER BY p.coin
        """
    )
    return jsonify(rows)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
