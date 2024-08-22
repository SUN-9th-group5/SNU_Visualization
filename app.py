import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta  # datetime 모듈 임포트


# 사이드바에서 페이지 선택
tab1, tab2, tab3 = st.tabs(["포트폴리오 분석", "재투자 분석", "포트폴리오 재투자 금액 차이 분석"])

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
