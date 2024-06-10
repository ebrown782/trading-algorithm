import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
import logging
import time
import asyncio
import aiohttp

# Setup logging
logging.basicConfig(filename='trading.log', level=logging.INFO, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Define your API credentials
API_KEY = 'your_api_key'
API_SECRET = 'your_api_secret'
BASE_URL = 'https://paper-api.alpaca.markets'

# Initialize the Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# Define parameters
symbol = 'AAPL'
short_window = 40
long_window = 100
initial_capital = 100000
transaction_cost = 0.001  # 0.1% per trade
risk_tolerance = 0.02  # Risk 2% of capital on each trade

running = False

# Fetch historical data
async def fetch_historical_data(session, symbol, start_date, end_date):
    url = f'{BASE_URL}/v2/stocks/{symbol}/bars?start={start_date}&end={end_date}'
    async with session.get(url) as response:
        data = await response.json()
        return pd.DataFrame(data['bars'])

# Fetch real-time data
async def fetch_real_time_data(session, symbol, timeframe='1Min', limit=200):
    url = f'{BASE_URL}/v2/stocks/{symbol}/bars?timeframe={timeframe}&limit={limit}'
    async with session.get(url) as response:
        data = await response.json()
        return pd.DataFrame(data['bars'])

# Calculate moving averages
def calculate_moving_averages(data, short_window, long_window):
    data['short_mavg'] = data['close'].rolling(window=short_window, min_periods=1).mean()
    data['long_mavg'] = data['close'].rolling(window=long_window, min_periods=1).mean()
    return data

# Generate trading signals
def generate_signals(data):
    data['signal'] = 0
    data['signal'][short_window:] = np.where(data['short_mavg'][short_window:] > data['long_mavg'][short_window:], 1, 0)
    data['positions'] = data['signal'].diff()
    return data

# Execute trade
async def execute_trade(signal, symbol, quantity):
    try:
        if signal == 1:
            await api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            logging.info(f"Bought {quantity} shares of {symbol}")
        elif signal == -1:
            await api.submit_order(
                symbol=symbol,
                qty=quantity,
                side='sell',
                type='market',
                time_in_force='gtc'
            )
            logging.info(f"Sold {quantity} shares of {symbol}")
    except Exception as e:
        logging.error(f"Trade execution failed: {e}")

# Calculate position size based on risk management
def calculate_position_size(current_price, capital, risk_tolerance):
    position_size = capital * risk_tolerance / current_price
    return int(position_size)

# Simulate trading
def simulate_trading(data, initial_capital, transaction_cost, risk_tolerance):
    capital = initial_capital
    positions = 0
    portfolio_value = []

    for i in range(len(data)):
        current_price = data['close'].iloc[i]
        signal = data['positions'].iloc[i]
        
        if signal == 1:
            position_size = calculate_position_size(current_price, capital, risk_tolerance)
            if capital >= position_size * current_price * (1 + transaction_cost):
                positions += position_size
                capital -= position_size * current_price * (1 + transaction_cost)
                logging.info(f"Simulated buy: {position_size} shares at {current_price}")
        
        elif signal == -1 and positions > 0:
            capital += positions * current_price * (1 - transaction_cost)
            logging.info(f"Simulated sell: {positions} shares at {current_price}")
            positions = 0

        portfolio_value.append(capital + positions * current_price)

    return portfolio_value

# Main trading loop
async def trading_loop():
    global running
    capital = initial_capital
    positions = 0
    
    async with aiohttp.ClientSession() as session:
        while running:
            try:
                data = await fetch_real_time_data(session, symbol)
                data = calculate_moving_averages(data, short_window, long_window)
                data = generate_signals(data)

                current_price = data['close'][-1]
                position_size = calculate_position_size(current_price, capital, risk_tolerance)

                last_signal = data['positions'][-1]
                if last_signal == 1 and capital >= position_size * current_price * (1 + transaction_cost):
                    await execute_trade(1, symbol, position_size)
                    capital -= position_size * current_price * (1 + transaction_cost)
                    positions += position_size
                elif last_signal == -1 and positions > 0:
                    await execute_trade(-1, symbol, positions)
                    capital += positions * current_price * (1 - transaction_cost)
                    positions = 0

                # Log current capital and positions
                logging.info(f"Current capital: ${capital:.2f}")
                logging.info(f"Current price: ${current_price:.2f}")
                logging.info(f"Position size: {position_size} shares")
                logging.info(f"Positions held: {positions} shares")

            except Exception as e:
                logging.error(f"Error in trading loop: {e}")

            await asyncio.sleep(60)  # Wait for a minute before next iteration

def start_trading():
    global running
    running = True
    loop = asyncio.get_event_loop()
    loop.run_until_complete(trading_loop())

def stop_trading():
    global running
    running = False
