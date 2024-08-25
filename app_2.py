import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta  # datetime 모듈 임포트
import matplotlib.pyplot as plt
from PIL import Image
import os
import itertools 
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from matplotlib.patches import Ellipse

# 사이드바에서 페이지 선택
tab1, tab2, tab3, tab4, tab5 = st.tabs(["포트폴리오 분석", "재투자 분석", "포트폴리오 재투자 금액 차이 분석",'나만의 배당주 포트폴리오 구성하기',"etf 성장률 그래프"])

def download_logo_to_file(url, filename):
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img.save(filename)
    except Exception as e:
        st.error(f"이미지를 다운로드하는 중 오류 발생: {e}")

# 페이지 1: 포트폴리오 분석

with tab1:
    st.title('나만의 월 배당 포트폴리오 구축')

    # 포트폴리오를 저장할 리스트
    if 'portfolio' not in st.session_state:
        st.session_state.portfolio = []

    # 초기 자본 입력받기 (단위: 달러)
    initial_capital = st.number_input('초기 자본을 입력하세요 (단위: 달러)', min_value=0.0, value=10000.0)  # 달러 단위로 입력

    # 남은 자본 계산 (포트폴리오에 추가된 주식들을 고려)
    if 'remaining_capital' not in st.session_state:
        st.session_state.remaining_capital = initial_capital
    else:
        st.session_state.remaining_capital = initial_capital - sum([stock['total_investment'] for stock in st.session_state.portfolio])

    # 남은 자본 표시
    st.write(f"남은 자본: ${st.session_state.remaining_capital:.2f}")

    # 주식 검색 및 주가 정보 가져오기
    ticker = st.text_input('주식 티커를 입력하세요 (예: AAPL, MSFT):')
    stock_price = None  # 주가를 저장할 변수 초기화

    # 주식 추가 기능
    if ticker:
        try:
            stock = yf.Ticker(ticker.upper())
            dividends = stock.dividends  # 배당금 데이터 가져오기
            stock_data = stock.history(period="1d")  # 최신 주가 데이터 가져오기

            if not dividends.empty and not stock_data.empty:
                latest_price = stock_data['Close'].iloc[-1]  # 최근 종가 가져오기
                st.write(f'현재 {ticker.upper()}의 주가는 ${latest_price:.2f}입니다.')
                
                if not dividends.empty:
                    latest_dividend = dividends.iloc[-1]  # 최신 배당금
                    st.write(f'현재 {ticker.upper()}의 최신 배당금: ${latest_dividend:.2f}')
                else:
                    st.write(f'{ticker.upper()}의 배당금 정보가 없습니다.')


                # 매수할 금액 입력받기
                investment_amount = st.number_input('매수할 금액을 입력하세요 (단위: 달러)', min_value=0.0, max_value=float(st.session_state.remaining_capital), step=100.0)
                
                # 남은 자본을 업데이트하여 표시
                st.write(f"매수 후 남은 자본: ${st.session_state.remaining_capital - investment_amount:.2f}")

                if investment_amount > 0 and investment_amount <= st.session_state.remaining_capital:
                    num_shares = investment_amount // latest_price  # 매수 가능한 주식 수
                    total_investment = num_shares * latest_price  # 총 투자 금액
                    
                    st.write(f'{investment_amount:.2f} 달러로 {num_shares:.2f} 주를 매수할 수 있습니다. (총 투자: ${total_investment:.2f})')

                    if st.button("매수"):
                        # 포트폴리오에 해당 주식 추가
                        st.session_state.portfolio.append({
                            'ticker': ticker.upper(),
                            'num_shares': num_shares,
                            'dividends': dividends * num_shares,  # 배당금에 주식 수 곱해서 반영
                            'total_investment': total_investment  # 총 투자 금액 반영
                        })
                        st.session_state.remaining_capital -= total_investment  # 남은 자본에서 차감
                        st.success(f'{ticker.upper()} 주식 {num_shares:.2f} 주가 포트폴리오에 추가되었습니다.')
                else:
                    st.warning(f"투자할 금액이 남은 자본을 초과하거나 유효하지 않습니다.")
            else:
                st.error(f'{ticker.upper()} 주식에 대한 배당금 데이터가 없습니다.')
        except Exception as e:
            st.error(f"데이터를 가져오는 중 오류 발생: {e}")

    # 포트폴리오에 추가된 주식 리스트 보여주기
    st.subheader('포트폴리오')
    if st.session_state.portfolio:
        # 각 주식의 배당금 정보를 모아서 하나의 DataFrame으로 구성
        portfolio_data = []
        for stock in st.session_state.portfolio:
            dividends = stock['dividends']
            for date, dividend in dividends.items():
                # 월을 1~12로 변환 (날짜의 월만 추출)
                month = pd.to_datetime(date).month
                portfolio_data.append({
                    'ticker': stock['ticker'],
                    'month': month,
                    'dividend': dividend
                })

        df = pd.DataFrame(portfolio_data)

        # X축에 12개월을 명시적으로 표시하도록 설정
        months = [str(i) for i in range(1, 13)]  # 1월부터 12월까지
        df['month'] = df['month'].astype(str)  # 월을 문자열로 변환하여 시각화에 사용

        # Plotly로 월별 배당금 누적 막대그래프 그리기
        fig = px.bar(
            df,
            x='month',
            y='dividend',
            color='ticker',
            hover_data=['ticker', 'dividend'],
            labels={'month': '월', 'dividend': '배당금 ($)'},
            title='포트폴리오의 월별 배당금 흐름',
            barmode='stack',  # 막대를 누적하여 표시
            category_orders={"month": months}  # X축에 1~12까지 표시
        )

        st.plotly_chart(fig)

        # 오른쪽에 포트폴리오 목록 표시
        st.sidebar.subheader('포트폴리오 목록')
        tickers_in_portfolio = [stock['ticker'] for stock in st.session_state.portfolio]
        st.sidebar.write(tickers_in_portfolio)

        # 주식 제거 기능 추가
        stock_to_remove = st.sidebar.selectbox('제거할 주식을 선택하세요:', tickers_in_portfolio)
        if st.sidebar.button('제거'):
            # 남은 자본에 제거된 주식의 투자 금액을 다시 추가
            for stock in st.session_state.portfolio:
                if stock['ticker'] == stock_to_remove:
                    st.session_state.remaining_capital += stock['total_investment']
                    break
            # 포트폴리오에서 해당 주식 제거
            st.session_state.portfolio = [stock for stock in st.session_state.portfolio if stock['ticker'] != stock_to_remove]
            st.sidebar.success(f'{stock_to_remove} 주식이 포트폴리오에서 제거되었습니다.')
            st.experimental_rerun()  # 변경사항을 즉시 반영하기 위해 페이지를 다시 로드합니다.
    else:
        st.info('포트폴리오에 주식을 추가하세요.')


# 페이지 2: 재투자 분석
with tab2:
    st.title('주식 배당금 및 재투자 분석')

    # 사용자 입력 받기
    ticker_for_reinvestment = st.text_input('재투자 분석할 주식의 티커를 입력하세요 (예: AAPL):')

    if ticker_for_reinvestment:
        try:
            # 주식의 전체 기간 데이터 불러오기
            stock = yf.Ticker(ticker_for_reinvestment.upper())
            full_data = stock.history(period="max", actions=True)

            if not full_data.empty:
                # 날짜 범위 설정 없이 자유롭게 선택 가능하도록 변경
                earliest_date = full_data.index.min().date()
                latest_date = pd.Timestamp.today().date() - timedelta(days=1)

                # 기간 선택기 추가 - 시작 날짜는 기업 데이터의 가장 이른 날짜로, 종료 날짜는 어제로 설정
                start_date = st.date_input("시작 날짜", value=earliest_date, min_value=earliest_date, max_value=latest_date)
                end_date = st.date_input("종료 날짜", value=latest_date, min_value=earliest_date, max_value=latest_date)
                if start_date > end_date:
                    st.error("시작 날짜는 종료 날짜보다 이전이어야 합니다.")
                else:
                    # 선택된 기간 동안의 데이터를 불러오기
                    stock_data = stock.history(start=start_date, end=end_date, actions=True)

                    if stock_data.empty:
                        st.error(f"티커 '{ticker_for_reinvestment}'에 대한 데이터가 없습니다.")
                    else:
                        # 배당금 데이터 추출
                        if 'Dividends' in stock_data.columns:
                            dividends = stock_data['Dividends'].fillna(0)
                        else:
                            st.warning("이 주식에 대한 배당금 데이터가 없습니다.")
                            dividends = pd.Series(index=stock_data.index, data=0)

                        # 배당금이 있는 데이터만 필터링
                        dividend_data = dividends[dividends > 0]

                        if dividend_data.empty:
                            st.warning("이 주식에 대한 배당금 데이터가 없습니다.")
                        else:
                            # 주가와 배당금 데이터 시뮬레이션
                            initial_shares = 1  # 초기 투자 시 주식 수
                            shares = pd.Series(index=stock_data.index, data=np.nan)
                            investment_value = pd.Series(index=stock_data.index, data=np.nan)

                            shares.iloc[0] = initial_shares
                            investment_value.iloc[0] = stock_data['Close'].iloc[0] * initial_shares

                            for i in range(1, len(stock_data)):
                                # 이전 값 가져오기
                                prev_shares = shares.iloc[i-1]

                                # 배당금 재투자
                                dividend = dividends.iloc[i]
                                if dividend > 0:
                                    new_shares = dividend / stock_data['Close'].iloc[i]
                                    shares.iloc[i] = prev_shares + new_shares
                                else:
                                    shares.iloc[i] = prev_shares

                                # 재투자 후 총 투자 가치
                                investment_value.iloc[i] = shares.iloc[i] * stock_data['Close'].iloc[i]

                            # 그래프 생성
                            fig = go.Figure()

                            # 주가 시계열 (종가) - 선 아래 색칠
                            fig.add_trace(go.Scatter(
                                x=stock_data.index,
                                y=stock_data['Close'],
                                mode='lines',
                                name='종가',
                                line=dict(color='blue', width=1),  # 얇은 실선
                                fill='tozeroy',  # 선 아래 색칠
                                fillcolor='rgba(0, 0, 255, 0.3)',  # 색상과 투명도 설정
                                yaxis='y1',
                                hovertemplate='주가: %{y:.2f}<extra></extra>'
                            ))

                            # 배당금 시계열 (막대그래프) - 굵기 조정
                            fig.add_trace(go.Bar(
                                x=dividend_data.index,
                                y=dividend_data,
                                name='배당금',
                                marker=dict(color='orange'),
                                opacity=0.6,  # 투명도 조정
                                width=15,  # 막대 너비 조정
                                yaxis='y2',
                                hovertemplate='배당금: %{y:.2f}<extra></extra>'
                            ))

                            # 재투자 후 주가 시계열 - 선 아래 색칠 및 색상 조정
                            fig.add_trace(go.Scatter(
                                x=investment_value.index,
                                y=investment_value,
                                mode='lines',
                                name='재투자 가치',
                                line=dict(color='green', width=1),  # 얇은 실선
                                fill='tozeroy',  # 선 아래 색칠
                                fillcolor='rgba(0, 255, 0, 0.3)',  # 색상과 투명도 설정
                                yaxis='y1',
                                hovertemplate='재투자 가치: %{y:.2f}<extra></extra>'
                            ))

                            # 그래프 레이아웃 설정
                            fig.update_layout(
                                title=f'{ticker_for_reinvestment} 주가, 배당금 및 재투자 가치',
                                xaxis_title='날짜',
                                yaxis_title='주가',
                                yaxis=dict(
                                    title='주가',
                                    titlefont=dict(color='black'),
                                    tickfont=dict(color='black'),
                                    range=[0, stock_data['Close'].max() * 1.5],  # 좌측 y축 범위 설정 (조정)
                                    autorange=False,
                                    title_standoff=20,  # 제목과 축 사이의 거리
                                    tickangle=-45  # x축 레이블 회전
                                ),
                                yaxis2=dict(
                                    title='배당금',
                                    titlefont=dict(color='black'),
                                    tickfont=dict(color='black'),
                                    overlaying='y',
                                    side='right',
                                    range=[0, 3],  # 오른쪽 y축 범위 설정
                                    title_standoff=20  # 제목과 축 사이의 거리
                                ),
                                hovermode='x unified',
                                barmode='overlay',  # 막대그래프와 선그래프 겹치게 표현
                                height=800,  # 그래프 높이 설정
                                margin=dict(t=50, b=150, l=70, r=70),  # 여백 조정
                                xaxis=dict(
                                    tickangle=-45,  # x축 레이블 회전
                                    tickfont=dict(size=10, color='black')  # x축 레이블 색상 조정
                                )
                            )

                            # 배경과 텍스트 색상 조정
                            fig.update_layout(
                                plot_bgcolor='white',
                                paper_bgcolor='lightgray',
                                font=dict(size=12, color='black')
                            )

                            # 그래프 보여주기
                            st.plotly_chart(fig)
            else:
                st.error(f"티커 '{ticker_for_reinvestment}'에 대한 데이터가 없습니다.")
        except Exception as e:
            st.error(f"데이터를 가져오는 중 오류 발생: {e}")

with tab3:
    st.title('포트폴리오 재투자 금액 차이 분석')

    # 포트폴리오가 존재하지 않으면 메시지 표시
    if 'portfolio' not in st.session_state or not st.session_state.portfolio:
        st.info('포트폴리오가 없습니다. 먼저 포트폴리오를 구성해 주세요.')
    else:
        # 포트폴리오 데이터 가져오기
        portfolio = st.session_state.portfolio

        # 초기 투자 금액 계산
        initial_investment = sum(stock['total_investment'] for stock in portfolio)
        st.write(f"초기 투자 금액: ${initial_investment:.2f}")

        # 가장 최근 날짜 찾기
        recent_date = pd.Timestamp.min
        for stock in portfolio:
            dividends = stock['dividends']
            if not dividends.empty:
                latest_date = pd.to_datetime(max(dividends.index)).tz_localize(None)  # 시간대 정보 제거
                if latest_date > recent_date:
                    recent_date = latest_date

        if recent_date == pd.Timestamp.min:
            st.error("포트폴리오에 배당금 데이터가 없습니다.")
        else:
            # 재투자 후 현재 포트폴리오 가치 계산
            total_current_value = 0.0
            for stock in portfolio:
                ticker = stock['ticker']
                num_shares = stock['num_shares']
                stock_data = yf.Ticker(ticker).history(start=recent_date, period="1d")  # 최근 가격 가져오기
                if not stock_data.empty:
                    latest_price = stock_data['Close'].iloc[-1]
                    total_current_value += num_shares * latest_price
                else:
                    st.warning(f"{ticker}의 주가 데이터를 가져오는 데 문제가 발생했습니다.")

            # 배당금 재투자 계산
            total_dividends = 0.0
            for stock in portfolio:
                dividends = stock['dividends']
                total_dividends += dividends.sum()  # 배당금 합계

            # 재투자 후 총 포트폴리오 가치 계산
            re_investment_value = total_current_value + total_dividends - initial_investment
            st.write(f"현재 포트폴리오의 총 가치: ${total_current_value:.2f}")
            st.write(f"배당금 재투자 합계: ${total_dividends:.2f}")
            st.write(f"재투자 금액 차이: ${re_investment_value:.2f}")

            if re_investment_value > 0:
                st.success(f"재투자 금액이 ${re_investment_value:.2f} 증가했습니다.")
            elif re_investment_value < 0:
                st.error(f"재투자 금액이 ${abs(re_investment_value):.2f} 감소했습니다.")
            else:
                st.info("재투자 금액의 차이가 없습니다.")
                # 페이지 4: 배당 포트폴리오 구축
with tab4:
    st.title("나만의 배당주 포트폴리오 구성하기")
    
    # 배당킹주와 배당귀족주 리스트 및 배당 월 정보
    dividend_king_stocks = {
        'MMM': ('3M', 'https://seeklogo.com/images/1/3M-logo-DCF26CFF14-seeklogo.com.png', [3, 6, 9, 12]),
        'KO': ('Coca-Cola', 'https://seeklogo.com/images/C/coca-cola-circle-logo-A9EBD3B00A-seeklogo.com.png', [1, 4, 7, 10]),
        'JNJ': ('Johnson & Johnson', 'https://seeklogo.com/images/J/johnson-johnson-logo-5912A7508E-seeklogo.com.png', [2, 5, 8, 11]),
        'PG': ('Procter & Gamble', 'https://seeklogo.com/images/P/p-g-logo-14BC19B5E7-seeklogo.com.png', [3, 6, 9, 12]),
        'CL': ('Colgate-Palmolive', 'https://seeklogo.com/images/C/colgate-palmolive-logo-63D53420E1-seeklogo.com.png', [1, 4, 7, 10]),
        'PEP': ('PepsiCo', 'https://seeklogo.com/images/P/pepsi-vertical-logo-72846897FF-seeklogo.com.png', [3, 6, 9, 12]),
        'GPC': ('Genuine Parts Company', 'https://seeklogo.com/images/G/genuine-parts-company-logo-23D67B3040-seeklogo.com.png', [3, 6, 9, 12]),
        'ABT': ('Abbott', 'https://g.foolcdn.com/art/companylogos/mark/ABT.png', [2, 5, 8, 11]),
        'PH': ('Parker Hannifin', 'https://seeklogo.com/images/P/Parker_Hannifin-logo-30D7790AEF-seeklogo.com.png', [2, 5, 8, 11]),
        'WBA': ('Walgreens Boots Alliance', 'https://seeklogo.com/images/W/Walgreens-logo-38D42E4EC1-seeklogo.com.png', [1, 4, 7, 10]),
        'LOW': ('Lowe’s', 'https://seeklogo.com/images/L/lowes-logo-BD8C045F2F-seeklogo.com.png', [2, 5, 8, 11]),
        'CLX': ('Clorox', 'https://seeklogo.com/images/C/Clorox-logo-88E4ED3C26-seeklogo.com.png', [3, 6, 9, 12]),
        'HRL': ('Hormel Foods', 'https://seeklogo.com/images/H/hormel-logo-2C9BC6463A-seeklogo.com.png', [1, 4, 7, 10]),
        'CVX': ('Chevron', 'https://seeklogo.com/images/C/Chevron_Corporation-logo-FFAC2E8206-seeklogo.com.png', [2, 5, 8, 11]),
        'EMR': ('Emerson Electric', 'https://seeklogo.com/images/E/Emerson_Electric-logo-CF7EACA482-seeklogo.com.png', [3, 6, 9, 12]),
        'SYY': ('Sysco', 'https://seeklogo.com/images/S/sysco-logo-7B5B009D80-seeklogo.com.png', [1, 4, 7, 10]),
        'SWK': ('Stanley Black & Decker', 'https://seeklogo.com/images/S/stanley-black-decker-logo-81E59F852A-seeklogo.com.png', [2, 5, 8, 11]),
        'AFL': ('Aflac', 'https://seeklogo.com/images/A/AFLAC-logo-EDE6C89650-seeklogo.com.png', [3, 6, 9, 12]),
        'SHW': ('Sherwin-Williams', 'https://seeklogo.com/images/S/Sherwin_Williams-logo-3FE71297BA-seeklogo.com.png', [1, 4, 7, 10]),
        'LLY': ('Eli Lilly', 'https://seeklogo.com/images/L/Lilly-logo-6EF04E4361-seeklogo.com.png', [2, 5, 8, 11]),
    }
    
    dividend_aristocrat_stocks = {
        'ADM': ('Archer Daniels Midland', 'https://seeklogo.com/images/A/archer-daniels-midland-company-logo-B4F247583E-seeklogo.com.png', [1, 4, 7, 10]),
        'ABBV': ('AbbVie', 'https://seeklogo.com/images/A/abbvie-logo-BEB7C12577-seeklogo.com.png', [2, 5, 8, 11]),
        'DOV': ('Dover', 'https://seeklogo.com/images/D/Dover-logo-2F344F6F42-seeklogo.com.png', [3, 6, 9, 12]),
        'ITW': ('Illinois Tool Works', 'https://seeklogo.com/images/I/illinois-tool-works-logo-FCB6FE9266-seeklogo.com.png', [1, 4, 7, 10]),
        'KMB': ('Kimberly-Clark', 'https://seeklogo.com/images/K/Kimberly-Clark_Sopalin-logo-8B40BD9217-seeklogo.com.png', [3, 6, 9, 12]),
        'XOM': ('ExxonMobil', 'https://seeklogo.com/images/E/Exxon-logo-6F21C176C8-seeklogo.com.png', [1, 4, 7, 10]),
        'MDT': ('Medtronic', 'https://seeklogo.com/images/M/medtronic-healthcare-logo-97942C1A14-seeklogo.com.png', [2, 5, 8, 11]),
        'WMT': ('Walmart', 'https://seeklogo.com/images/W/walmart-spark-logo-57DC35C86C-seeklogo.com.png', [1, 4, 7, 10]),
        'TROW': ('T. Rowe Price', 'https://seeklogo.com/images/T/trow-logo-5361227321-seeklogo.com.png', [2, 5, 8, 11]),
        'APD': ('Air Products and Chemicals', 'https://seeklogo.com/images/A/Air_Products_and_Chemicals-logo-ACDA8A1C8B-seeklogo.com.png', [1, 4, 7, 10]),
        'BF-B': ('Brown-Forman', 'https://seeklogo.com/images/B/brown-forman-logo-B919105D7B-seeklogo.com.png', [2, 5, 8, 11]),
        'CINF': ('Cincinnati Financial', 'https://seeklogo.com/images/C/cincinnati-financial-logo-A2A7957DB1-seeklogo.com.png', [3, 6, 9, 12]),
        'CTAS': ('Cintas', 'https://seeklogo.com/images/C/cintas-logo-0F4637C8B8-seeklogo.com.png', [1, 4, 7, 10]),
        'ED': ('Consolidated Edison', 'https://seeklogo.com/images/C/consolidated-edison-logo-F23BE97D80-seeklogo.com.png', [2, 5, 8, 11]),
        'GWW': ('Grainger', 'https://seeklogo.com/images/G/grainger-logo-C959D21C07-seeklogo.com.png', [1, 4, 7, 10]),
        'MKC': ('McCormick', 'https://seeklogo.com/images/M/McCormick-logo-144428A8DB-seeklogo.com.png', [3, 6, 9, 12]),
        'NUE': ('Nucor', 'https://seeklogo.com/images/N/Nucor-logo-E63140A596-seeklogo.com.png', [2, 5, 8, 11]),
        'ROP': ('Roper Technologies', 'https://seeklogo.com/images/R/Roper-logo-73AE49CBF0-seeklogo.com.png', [3, 6, 9, 12]),
        'SPGI': ('S&P Global', 'https://seeklogo.com/images/S/s-p-global-logo-62660CED63-seeklogo.com.png', [1, 4, 7, 10]),
        'TGT': ('Target', 'https://seeklogo.com/images/T/Target-logo-9FE48EBE3B-seeklogo.com.png', [2, 5, 8, 11]),
        'MCD': ('McDonald’s', 'https://seeklogo.com/images/M/mcdonald-s-golden-arches-logo-93483062BF-seeklogo.com.png', [3, 6, 9, 12]),
    }
    if 'selected_companies' not in st.session_state:
        st.session_state['selected_companies'] = []
    
    # Create placeholder for chart area
    chart_placeholder = st.empty()
    
    # Function to draw the chart
    def draw_chart():
        fig, ax = plt.subplots(figsize=(12, 7))  # Adjust chart size
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        ax.set_xticks(range(1, 13))
        ax.set_xticklabels(months, fontsize=12, rotation=45)  # Rotate x-axis labels and adjust font size
        ax.set_xlim(0.5, 12.5)
        ax.set_ylim(-0.5, max(5, len(st.session_state.selected_companies)))  # Dynamic y-axis size
        ax.grid(True, linestyle='--', alpha=0.6)  # Adjust grid style
        ax.set_title("Dividend Portfolio", fontsize=18, fontweight='bold', pad=20)  # Add chart title
        ax.legend(loc='upper right', fontsize=12)
    
        # Add logos for selected stocks
        if st.session_state.selected_companies:
            company_names = [
                (dividend_king_stocks[company][0] if category == 'king' else dividend_aristocrat_stocks[company][0])
                for company, category in st.session_state.selected_companies
            ]
            ax.set_yticks(range(len(st.session_state.selected_companies)))
            ax.set_yticklabels(company_names, fontsize=12, fontweight='bold')  # Adjust y-axis label style
    
            for idx, (company, category) in enumerate(st.session_state.selected_companies):
                dividend_months = (dividend_king_stocks[company][2] if category == 'king' else dividend_aristocrat_stocks[company][2])
                logo_url = (dividend_king_stocks[company][1] if category == 'king' else dividend_aristocrat_stocks[company][1])
                logo_filename = f"{company}_logo.png"
    
                # Download logo if it doesn't exist
                if not os.path.exists(logo_filename):
                    download_logo_to_file(logo_url, logo_filename)
    
                # Load logo image from local file
                if os.path.exists(logo_filename):
                    logo_image = Image.open(logo_filename).resize((40, 40))  # Resize
    
                    # Display logo on the chart
                    for month in dividend_months:
                        ax.imshow(logo_image, extent=(month-0.35, month+0.35, idx-0.25, idx+0.25), aspect='auto')
    
        # Update chart in the placeholder
        chart_placeholder.pyplot(fig)
        plt.close(fig)  # Close the chart to prevent memory leaks
    
    # Create a mapping of tickers to company names
    ticker_to_name_king = {ticker: name for ticker, (name, _, _) in dividend_king_stocks.items()}
    ticker_to_name_aristocrat = {ticker: name for ticker, (name, _, _) in dividend_aristocrat_stocks.items()}
    
    king_selection = st.selectbox("배당킹주에서 선택", ['선택하세요'] + list(ticker_to_name_king.values()), key='select_king')
    if st.button("추가", key='add_king') and king_selection != '선택하세요':
        ticker = [ticker for ticker, name in ticker_to_name_king.items() if name == king_selection][0]
        st.session_state.selected_companies.append((ticker, 'king'))
        draw_chart()  # Update the chart
    
    aristocrat_selection = st.selectbox("배당귀족주에서 선택", ['선택하세요'] + list(ticker_to_name_aristocrat.values()), key='select_aristocrat')
    if st.button("추가", key='add_aristocrat') and aristocrat_selection != '선택하세요':
        ticker = [ticker for ticker, name in ticker_to_name_aristocrat.items() if name == aristocrat_selection][0]
        st.session_state.selected_companies.append((ticker, 'aristocrat'))
        draw_chart()  # Update the chart
    
    # Remove stock from portfolio
    remove_company = st.selectbox("제거할 주식 선택", ['선택하세요'] + [ticker_to_name_king.get(company, '') for company, _ in st.session_state.selected_companies] + [ticker_to_name_aristocrat.get(company, '') for company, _ in st.session_state.selected_companies], key='remove_select')
    if st.button("제거", key='remove_company') and remove_company != '선택하세요':
        ticker_to_remove = [ticker for ticker, name in ticker_to_name_king.items() if name == remove_company] + [ticker for ticker, name in ticker_to_name_aristocrat.items() if name == remove_company]
        st.session_state.selected_companies = [(company, category) for company, category in st.session_state.selected_companies if company not in ticker_to_remove]
        st.success(f"{remove_company}이(가) 포트폴리오에서 제거되었습니다.")
        draw_chart()  # Update the chart
    
    # Display an empty chart initially
    draw_chart()

with tab5:
    st.title("ETF 성장률 그래프")
    years = list(range(2006, 2024))  # 2006년부터 2023년까지, 총 18개
    


    data33 = {
        'Year': years,
        'SCHD_AUM': [None]*5 + [2.5, 4.0, 6.5, 9.2, 13.5, 18.3, 22.5, 27.8, 35.0, 45.5, 52.8, 60.4, 65.0],  # 총 18개로 맞춤
        'VIG_AUM': [1.5, 3.0, 4.5, 6.0, 7.5, 10.0, 12.5, 15.0, 18.5, 20.0, 22.0, 25.0, 30.0, 35.0, 40.0, 50.0, 60.0, 65.5],  # 총 18개로 맞춤
        'JEPI_AUM': [None]*14 + [18.7, 25.2, 30.33, 32],  # 총 18개로 맞춤
        'DGRW_AUM': [None]*7 + [5.0, 7.5, 10.0, 12.5, 15.0, 18.5, 20.3, 24.0, 28.1, 30.4, 32.2],  # 총 18개
        'NOBL_AUM': [None]*7 + [2.0, 5.0, 7.5, 10.5, 12.0, 15.0, 18.3, 22.1, 25.4, 27.5, 29.0]  # 총 18개
    }
        
    # 모든 리스트의 길이가 동일한지 확인
    for key, value in data33.items():
        if len(value) != len(years):
            raise ValueError(f"{key}의 길이가 {len(value)}로 {len(years)}와 일치하지 않습니다.")
    
    df_33 = pd.DataFrame(data33)
    
    # 사이드바에서 기간 설정 슬라이더 추가
    min_year, max_year = 2006, 2023  # 2006년부터 설정 가능
    selected_year = st.sidebar.slider('Select Year', min_value=min_year, max_value=max_year, value=min_year)
    
    # 사이드바에서 ETF 선택
    etf_options = ['SCHD', 'VIG', 'JEPI', 'DGRW', 'NOBL']
    selected_etf = st.sidebar.selectbox("Select an ETF", etf_options)
    
    # 선택한 ETF 열 이름 생성
    aum_column = f'{selected_etf}_AUM'
    
    # 데이터프레임에 해당 열이 있는지 확인
    if aum_column in df_33.columns:
        # 최초 설정액 및 선택한 연도의 설정액 가져오기
        initial_aum = df_33[aum_column].dropna().iloc[0]  # 첫 번째 유효값 (최초 설정액)
        initial_year = df_33['Year'][df_33[aum_column].notna()].iloc[0]  # 첫 번째 유효값의 연도
    
        # 선택한 연도에 ETF가 존재하지 않으면 문구 출력
        if selected_year < initial_year:
            st.write(f"이 ETF는 {initial_year}년에 설정되었습니다.")
            selected_aum = None
        else:
            selected_aum = df_33[df_33['Year'] == selected_year][aum_column].values[0]
    else:
        st.error(f"{selected_etf}의 데이터가 존재하지 않습니다.")
        initial_aum = None
        selected_aum = None
    
    # 두 개의 동그라미를 시각화 (최초 설정액과 선택한 연도의 설정액)
    fig = go.Figure()
    
    # 왼쪽 동그라미 (최초 설정액) - 금액 표시, 글자 크기를 줄여서 표시, 동그라미 크기 9로 설정
    if initial_aum is not None:
        fig.add_trace(go.Scatter(
            x=[0.5], y=[0],
            mode='markers+text',
            marker=dict(size=initial_aum * 12, color='lightblue'),  # 동그라미 크기를 9로 설정
            text=[f'{initial_aum}B$'],  # 금액으로 변경
            textposition='middle center',
            textfont=dict(color='black', size=14),  # 글자 크기를 줄임
            name='Initial AUM'
        ))
    
    # 오른쪽 동그라미 (선택한 연도의 AUM) - 존재할 경우만 표시
    if selected_aum is not None:
        fig.add_trace(go.Scatter(
            x=[1.5], y=[0],
            mode='markers+text',
            marker=dict(size=selected_aum * 12, color='blue'),
            text=[f'{selected_aum}B$'],
            textposition='middle center',
            textfont=dict(size=selected_aum * 1.5, color='white'),  # 숫자 크기 조정
            name='Selected AUM'
        ))
    
    # 두 동그라미 사이에 화살표 추가 (가운데 배치, 크기와 두께 증가, 색상 흰색)
    fig.add_annotation(
        x=1, y=0,
        ax=1, ay=0,
        xref="x", yref="y",
        axref="x", ayref="y",
        showarrow=True,
        arrowhead=2,
        arrowsize=3,  # 화살표 크기 증가
        arrowwidth=4,  # 화살표 두께 증가
        arrowcolor="white"  # 화살표 색상 흰색
    )
    
    # 아래 텍스트 추가 (최초 설정 연도 및 선택한 연도의 설정액)
    if initial_aum is not None:
        fig.add_annotation(
            text=f"{initial_year}년 최초 설정액", 
            x=0.5, y=-0.2, showarrow=False,
            font=dict(size=14),
            xanchor='center'
        )
    
    if selected_aum is not None:
        fig.add_annotation(
            text=f"{selected_year}년 설정액", 
            x=1.5, y=-0.2, showarrow=False,
            font=dict(size=14),
            xanchor='center'
        )
    
    # 레이아웃 설정 - 차트가 잘리지 않도록 높이와 너비 조정
    fig.update_layout(
        title=f'{selected_etf} AUM Over Time',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[0, 2]),  # 동그라미가 차트 안에 들어오도록 조정
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-1, 1]),
        showlegend=False,
        height=600,  # 높이 조정
        width=1000  # 너비 조정
    )
    
    # 그래프 출력
    st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.title("3M 로고 이미지 테스트")
    
    # 3M 로고 URL과 파일명
    logo_url = "https://seeklogo.com/images/A/apple-logo-52C416BDDD-seeklogo.com.png"
    logo_filename = "3M_logo.png"
    
    # 파일이 없으면 다운로드
    if not os.path.exists(logo_filename):
        download_logo_to_file(logo_url, logo_filename)
    
    # 로컬에서 로고 이미지를 불러오기
    if os.path.exists(logo_filename):
        logo_image = Image.open(logo_filename)
        st.image(logo_image, caption="3M Logo", use_column_width=True)
    else:
        st.error("로고 이미지를 불러올 수 없습니다.")
