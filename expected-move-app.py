import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
from datetime import date


st.set_page_config(page_title="Expected Move Calculator")

st.title("📈 Stock Expected Move Calculator (Binary Event)")

stock_symbol = st.text_input("Enter Stock Symbol (e.g., AAPL)", "AAPL").upper()
exp_date = st.date_input("Select Option Expiration Date", value=date.today())

# Convert date to string format for yfinance
expiration_date = exp_date.strftime('%Y-%m-%d')

def find_nearest_strike(strikes, spot):
    return min(strikes, key=lambda x: abs(x - spot))

def calculate_expected_move(symbol, date_str):
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        st.error("Invalid date format. Please use YYYY-MM-DD.")
        return

    ticker = yf.Ticker(symbol)
    spot = ticker.history(period="1d")['Close'][-1]

    try:
        chain = ticker.option_chain(date_str)
    except Exception as e:
        st.error(f"Could not fetch option chain: {e}")
        return

    calls = chain.calls
    puts = chain.puts

    atm_strike = find_nearest_strike(calls['strike'], spot)

    try:
        # ATM Straddle
        atm_call_price = calls[calls['strike'] == atm_strike]['lastPrice'].values[0]
        atm_put_price = puts[puts['strike'] == atm_strike]['lastPrice'].values[0]
        straddle = atm_call_price + atm_put_price

        # First OTM Strangle
        higher_calls = sorted([s for s in calls['strike'] if s > atm_strike])
        lower_puts = sorted([s for s in puts['strike'] if s < atm_strike])

        if not higher_calls or not lower_puts:
            st.warning("Not enough OTM strikes available.")
            return

        otm_call_strike = higher_calls[0]
        otm_put_strike = lower_puts[-1]

        otm_call_price = calls[calls['strike'] == otm_call_strike]['lastPrice'].values[0]
        otm_put_price = puts[puts['strike'] == otm_put_strike]['lastPrice'].values[0]
        strangle = otm_call_price + otm_put_price

        expected_move = round((straddle + strangle) / 2, 2)

        st.subheader(f"Results for {symbol} (Exp: {date_str})")
        st.write(f"Spot Price: **${spot:.2f}**")
        st.write(f"ATM Strike: **{atm_strike}**")
        st.write(f"ATM Straddle: ${straddle:.2f}")
        st.write(f"1st OTM Strangle (Call {otm_call_strike}, Put {otm_put_strike}): ${strangle:.2f}")
        st.success(f"📊 Expected Move ≈ **${expected_move}**")
        # Create chart data
        df = pd.DataFrame({
            'Price Point': ['Lower Bound', 'Current Price', 'Upper Bound'],
            'Value': [spot - expected_move, spot, spot + expected_move]
        })

        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X('Price Point', sort=['Lower Bound', 'Current Price', 'Upper Bound']),
            y='Value',
            tooltip=['Price Point', 'Value']
        ).properties(
            title='Expected Move Range'
        )
        
        st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        st.error(f"Calculation error: {e}")

# Trigger on button click
if st.button("Calculate Expected Move"):
    calculate_expected_move(stock_symbol, expiration_date)
