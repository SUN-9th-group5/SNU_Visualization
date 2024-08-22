import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Streamlit 페이지 설정
st.set_page_config(page_title="Stock Analysis", layout="wide")

# 인트로 페이지 함수
def intro_page():
    st.title("Build Wealth Today, Earn Income Tomorrow: The Power of Dividend Investing")
    # 이미지 표시 (로컬 이미지 파일 경로 또는 URL 사용)
    st.image("/Users/yej/Downloads/background.png", use_column_width=True)
    # 버튼
    if st.button("About Dividend"):
        st.session_state.page = "dividend"
    if st.button("Start"):
        st.session_state.page = "main"
    if st.button("투자성향 확인하기"):
        st.session_state.page = "invest"
    

# 본 페이지 함수
def main_page():
    st.title("Stock Analysis with Dividends Reinvestment")
    ticker = st.text_input("Enter stock ticker", "AAPL")
    period = st.selectbox("Select period", ["1y", "5y", "10y"])

    # 데이터 다운로드
    @st.cache(allow_output_mutation=True)
    def load_data(ticker, period):
        stock = yf.Ticker(ticker)
        stock_data = stock.history(period=period, actions=True)
        return stock_data

    stock_data = load_data(ticker, period)
    # 데이터 처리
    stock_data['Dividend'] = stock_data['Dividends'].fillna(0)
    stock_data['Price'] = stock_data['Close']

    # 배당금 및 주가 시뮬레이션
    initial_shares = 1
    shares = initial_shares
    price_list = []
    dividend_list = []
    investment_value = []

    for idx, row in stock_data.iterrows():
        dividends = row['Dividend']
        price = row['Price']

        # 재투자된 주식 수
        shares += (dividends / price)

        # 주가와 투자 가치 저장
        price_list.append(price)
        dividend_list.append(dividends)
        investment_value.append(shares * price)

    # 데이터 프레임 생성
    simulated_data = pd.DataFrame({
        'Date': stock_data.index,
        'Price': price_list,
        'Dividend': dividend_list,
        'Investment Value': investment_value
    })

    # 그래프 그리기
    fig, ax1 = plt.subplots(figsize=(14, 7))

    # 주가 선 그래프
    ax1.plot(simulated_data['Date'], simulated_data['Price'], color='tab:blue', label='Stock Price')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Stock Price', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    # 재투자 후 투자 가치 선 그래프
    ax2 = ax1.twinx()
    ax2.plot(simulated_data['Date'], simulated_data['Investment Value'], color='tab:green', linestyle='--', label='Investment Value')
    ax2.set_ylabel('Investment Value', color='tab:green')
    ax2.tick_params(axis='y', labelcolor='tab:green')

    # 배당금 막대 그래프
    fig.tight_layout()
    ax1.bar(simulated_data['Date'], simulated_data['Dividend'], color='tab:orange', alpha=0.5, label='Dividend')

    # 범례 추가
    fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
    # Streamlit에 그래프 표시
    st.pyplot(fig)


# 설명 페이지 함수
def dividend_page():
    st.title("What is Dividend?")
    st.image("/Users/yej/Downloads/dividend.jpg", use_column_width=True)
    st.sidebar.header('입력')
    user_emoji = st.sidebar.selectbox('이모티콘 선택', ['', '😄', '😆', '😊', '😍', '😴', '😕', '😱'])


#투자성향 테스트 페이지 함수
def invest_page() : 
    st.title("나의 투자성향 알아보기")
    st.image("/Users/yej/Downloads/invest.jpg", use_column_width=True)


# 페이지 전환 로직
if "page" not in st.session_state:
    st.session_state.page = "intro"

if st.session_state.page == "intro":
    intro_page()
elif st.session_state.page == "main":
    main_page()
elif st.session_state.page == "dividend":
    dividend_page()
elif st.session_state.page == "invest":
    invest_page()