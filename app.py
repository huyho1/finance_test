from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, time

app = Flask(__name__)

def load_russell_3000():
    try:
        df = pd.read_csv('russell_3000.csv')
        return df.to_dict(orient='records')
    except Exception as e:
        print(f"Error loading Russell 3000 components: {e}")
        return []

top_us_stocks = load_russell_3000()

@app.route("/", methods=["GET", "POST"])
def index():
    error_message = None
    return render_template("index.html", error_message=error_message)

@app.route("/get_symbols", methods=["GET"])
def get_symbols():
    query = request.args.get("query", "").upper()
    if not query:
        return jsonify([])

    filtered_symbols = [
        f"{stock['Symbol']}, {stock['Name']}" for stock in top_us_stocks 
        if stock['Symbol'].startswith(query) or stock['Name'].upper().startswith(query)
    ][:5]

    return jsonify(filtered_symbols)

@app.route("/get_price", methods=["GET"])
def get_price():
    symbol = request.args.get("symbol", "")
    if not symbol or not any(stock['Symbol'] == symbol for stock in top_us_stocks):
        return jsonify({"error": "Please select a valid stock."}), 400

    stock = yf.Ticker(symbol)
    stock_info = stock.history(period="1d")
    
    if not stock_info.empty:
        stock_price = stock_info['Close'].iloc[-1]
        return jsonify({"price": stock_price})
    else:
        return jsonify({"error": "Stock data not available"}), 404

@app.route("/get_chart_data", methods=["GET"])
def get_chart_data():
    symbol = request.args.get("symbol", "")
    range = request.args.get("range", "1d")  # Default to '1d' if not provided

    if not symbol or not any(stock['Symbol'] == symbol for stock in top_us_stocks):
        return jsonify({"error": "Please select a valid stock."}), 400

    stock = yf.Ticker(symbol)

    # Check requested range and set appropriate period and interval
    if range == "1d":
        stock_info = stock.history(period="1d", interval="1m")
        
        if not stock_info.empty:
            # Fill missing time intervals
            all_times = pd.date_range(start=stock_info.index.min(), end=stock_info.index.max(), freq="1min", tz="America/New_York")
            stock_info = stock_info.reindex(all_times, method="ffill")
            
            labels = stock_info.index.strftime('%H:%M').tolist()  # Intraday timestamps
            prices = stock_info['Close'].tolist()
            return jsonify({"labels": labels, "prices": prices})

    elif range == "5d":
        stock_info = stock.history(period="5d", interval="15m")

        if not stock_info.empty:
            # Convert timezone to 'America/New_York'
            stock_info.index = stock_info.index.tz_convert("America/New_York")

            # Define market times for each day
            market_times = [
                "09:30", "09:45", "10:00", "10:15", "10:30", "10:45", "11:00", "11:15", 
                "11:30", "11:45", "12:00", "12:15", "12:30", "12:45", "13:00", "13:15", 
                "13:30", "13:45", "14:00", "14:15", "14:30", "14:45", "15:00", "15:15", 
                "15:30", "15:45", "16:00"
            ]

            # Filter for market hours on weekdays
            stock_info = stock_info[stock_info.index.strftime('%H:%M').isin(market_times)]
            stock_info = stock_info[stock_info.index.dayofweek < 5]  # Exclude weekends

            labels = stock_info.index.strftime('%Y-%m-%d %H:%M').tolist()
            prices = stock_info['Close'].tolist()
            return jsonify({"labels": labels, "prices": prices})

    elif range == "1mo":
        stock_info = stock.history(period="1mo", interval="1d")
        
        if not stock_info.empty:
            # Ensure the index is in the 'America/New_York' timezone
            stock_info.index = stock_info.index.tz_convert("America/New_York")

            # Filter out weekends
            stock_info = stock_info[stock_info.index.dayofweek < 5]  # Exclude weekends

            # For 1-month view, no need to fill missing times
            labels = stock_info.index.strftime('%Y-%m-%d').tolist()  # Daily timestamps
            prices = stock_info['Close'].tolist()
            return jsonify({"labels": labels, "prices": prices})
        
    elif range == "1y":
        stock_info = stock.history(period="1y", interval="1d")
        
        if not stock_info.empty:
            # Ensure the index is in the 'America/New_York' timezone
            stock_info.index = stock_info.index.tz_convert("America/New_York")

            # Filter out weekends
            stock_info = stock_info[stock_info.index.dayofweek < 5]  # Exclude weekends

            # For 1-month view, no need to fill missing times
            labels = stock_info.index.strftime('%Y-%m-%d').tolist()  # Daily timestamps
            prices = stock_info['Close'].tolist()
            return jsonify({"labels": labels, "prices": prices})
        
    elif range == "5y":
        stock_info = stock.history(period="5y", interval="1d")
        
        if not stock_info.empty:
            # Ensure the index is in the 'America/New_York' timezone
            stock_info.index = stock_info.index.tz_convert("America/New_York")

            # Filter out weekends
            stock_info = stock_info[stock_info.index.dayofweek < 5]  # Exclude weekends

            # For 1-month view, no need to fill missing times
            labels = stock_info.index.strftime('%Y-%m-%d').tolist()  # Daily timestamps
            prices = stock_info['Close'].tolist()
            return jsonify({"labels": labels, "prices": prices})

    # If stock data is empty or range is invalid, return error
    return jsonify({"error": "Stock data not available"}), 404

if __name__ == "__main__":
    app.run(debug=True)
