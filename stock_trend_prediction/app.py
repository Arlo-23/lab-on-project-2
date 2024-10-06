from flask import Flask, render_template, request
import requests
import pandas as pd
import plotly.graph_objs as go

app = Flask(__name__)

API_KEY = 'WCZ9J8QYGZ1FJI4L'  # Replace with your Alpha Vantage API key
CURRENCY_API_URL = 'https://api.exchangerate-api.com/v4/latest/'  # Base URL for exchange rates

def fetch_exchange_rate(base_currency, target_currency):
    url = f"{CURRENCY_API_URL}{base_currency}"
    response = requests.get(url)
    data = response.json()
    
    if 'rates' in data and target_currency in data['rates']:
        return data['rates'][target_currency]
    return None

def fetch_stock_data(stock_symbol, currency):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock_symbol}&apikey={API_KEY}&datatype=json"
    response = requests.get(url)
    data = response.json()
    
    if 'Error Message' in data:
        return None, f"Error: {data['Error Message']}"
    if 'Time Series (Daily)' not in data:
        return None, "Error fetching data. Please check the stock symbol."

    df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df.index = pd.to_datetime(df.index)
    df = df.astype(float)

    # Get exchange rate
    exchange_rate = fetch_exchange_rate('USD', currency)
    if exchange_rate is None:
        return None, "Error fetching exchange rate."

    # Convert prices to selected currency
    df[['open', 'high', 'low', 'close']] *= exchange_rate

    return df, None

def create_plots(df, stock_symbol, currency):
    # Create a list to hold the plot HTML
    plot_divs = []

    # Create a figure for open and close prices
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df.index, y=df['open'], mode='lines', name='Open (' + currency + ')'))
    fig1.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Close (' + currency + ')'))
    fig1.update_layout(title=f'Open and Close Prices for {stock_symbol} ({currency})',
                       xaxis_title='Date',
                       yaxis_title='Price (' + currency + ')',
                       template='plotly_dark')
    plot_divs.append(fig1.to_html(full_html=False))

    # Create a figure for high and low prices
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=df['high'], mode='lines', name='High (' + currency + ')'))
    fig2.add_trace(go.Scatter(x=df.index, y=df['low'], mode='lines', name='Low (' + currency + ')'))
    fig2.update_layout(title=f'High and Low Prices for {stock_symbol} ({currency})',
                       xaxis_title='Date',
                       yaxis_title='Price (' + currency + ')',
                       template='plotly_dark')
    plot_divs.append(fig2.to_html(full_html=False))

    # Create a figure for all four prices
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df.index, y=df['open'], mode='lines', name='Open (' + currency + ')'))
    fig3.add_trace(go.Scatter(x=df.index, y=df['high'], mode='lines', name='High (' + currency + ')'))
    fig3.add_trace(go.Scatter(x=df.index, y=df['low'], mode='lines', name='Low (' + currency + ')'))
    fig3.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='Close (' + currency + ')'))
    fig3.update_layout(title=f'All Prices for {stock_symbol} ({currency})',
                       xaxis_title='Date',
                       yaxis_title='Price (' + currency + ')',
                       template='plotly_dark')
    plot_divs.append(fig3.to_html(full_html=False))

    return plot_divs

@app.route('/', methods=['GET', 'POST'])
def index():
    prediction = None
    error = None
    plot_divs = []

    if request.method == 'POST':
        stock_symbol = request.form.get('stock_symbol')  # Use .get() to avoid KeyError
        currency = request.form.get('currency')          # Use .get() to avoid KeyError
        
        if not stock_symbol or not currency:
            error = "Please provide both stock symbol and currency."
        elif not stock_symbol.isalpha() or len(stock_symbol) > 5:
            error = "Invalid stock symbol. Please enter a valid symbol."
        else:
            df, api_error = fetch_stock_data(stock_symbol, currency)
            if df is None:
                error = api_error
            else:
                plot_divs = create_plots(df, stock_symbol, currency)

    return render_template('index.html', plot_divs=plot_divs, prediction=prediction, error=error)


if __name__ == "__main__":
    app.run(debug=True)
