import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 설정
st.set_page_config(page_title="2025 미세먼지 시각화 대시보드", layout="wide")

# 2. 데이터 로드 (캐싱을 통해 속도 향상)
@st.cache_data
def load_data():
    # 데이터 읽기 (제공된 파일 형식에 맞춰 로드)
    df = pd.read_csv("202501-air.csv")
    
    # 측정일시를 datetime 객체로 변환 (예: 2025010101 -> 2025-01-01 01:00)
    df['측정일시'] = pd.to_datetime(df['측정일시'], format='%Y%m%d%H')
    
    # '지역'에서 시/도 정보 추출 (첫 번째 단어)
    df['시도'] = df['지역'].apply(lambda x: x.split()[0])
    return df

try:
    df = load_data()

    # 3. 사이드바 - 필터링
    st.sidebar.header("🔍 필터 설정")
    selected_sido = st.sidebar.multiselect(
        "확인하고 싶은 시/도를 선택하세요",
        options=df['시도'].unique(),
        default=['서울']
    )

    filtered_df = df[df['시도'].isin(selected_sido)]

    # 4. 메인 화면 구성
    st.title("🌬️ 2025년 1월 전국 대기질 분석 대시보드")
    st.markdown(f"선택된 지역의 **미세먼지(PM10)** 및 **초미세먼지(PM2.5)** 현황을 시각화합니다.")

    # KPI 지표 (평균 농도)
    col1, col2, col3 = st.columns(3)
    avg_pm10 = filtered_df['PM10'].mean()
    avg_pm25 = filtered_df['PM25'].mean()
    
    col1.metric("평균 PM10", f"{avg_pm10:.2f} ㎍/㎥")
    col2.metric("평균 PM25", f"{avg_pm25:.2f} ㎍/㎥")
    col3.metric("총 측정 데이터 수", f"{len(filtered_df):,}건")

    st.divider()

    # 5. 시각화 - 시계열 차트
    st.subheader("📈 시간별 농도 변화 추이")
    pollutant = st.selectbox("분석할 오염물질 선택", ['PM10', 'PM25', 'O3', 'NO2'])
    
    # 지역별로 묶어서 시계열 그래프 생성
    fig_line = px.line(
        filtered_df, 
        x='측정일시', 
        y=pollutant, 
        color='측정소명',
        title=f"지역별 {pollutant} 변화량",
        template="plotly_white"
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # 6. 시각화 - 지역별 비교 (Box Plot)
    st.subheader("📊 지역별 농도 분포 비교")
    fig_box = px.box(
        filtered_df, 
        x='시도', 
        y=pollutant, 
        color='시도',
        points="all",
        title=f"시도별 {pollutant} 통계량"
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # 7. 데이터 테이블 보기
    if st.checkbox("전체 데이터 테이블 표시"):
        st.dataframe(filtered_df)

except FileNotFoundError:
    st.error("데이터 파일(202501-air.csv)을 찾을 수 없습니다. 파일 이름을 확인해 주세요.")
