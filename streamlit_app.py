import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 페이지 설정
st.set_page_config(page_title="2025년 1월 대기질 데이터 대시보드", layout="wide")

# 데이터 로드 함수
@st.cache_data
def load_data():
    # 파일 경로 설정 (Streamlit Cloud 환경 대응)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "202501-air.csv")
    
    if not os.path.exists(file_path):
        st.error(f"데이터 파일을 찾을 수 없습니다: {file_path}")
        return None

    # CSV 로드 (encoding은 일반적인 한국어 CSV 포맷인 cp949 혹은 utf-8 시도)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp949')

    # '측정일시'를 날짜 형식으로 변환 (YYYYMMDDHH)
    df['측정일시'] = pd.to_datetime(df['측정일시'], format='%Y%m%d%H')
    
    # '지역' 컬럼에서 '서울', '경남' 등 시도 정보 추출
    df['시도'] = df['지역'].apply(lambda x: x.split()[0])
    
    return df

# 데이터 불러오기
df = load_data()

if df is not None:
    # 사이드바 설정
    st.sidebar.header("📊 필터 옵션")
    
    # 시도 선택
    sido_list = sorted(df['시도'].unique())
    selected_sido = st.sidebar.multiselect("조회할 시도 선택", sido_list, default=[sido_list[0]])

    # 선택된 시도에 따른 측정소 필터
    filtered_df = df[df['시도'].isin(selected_sido)]
    station_list = sorted(filtered_df['측정소명'].unique())
    selected_stations = st.sidebar.multiselect("측정소 선택 (비워두면 전체 조회)", station_list)

    if selected_stations:
        filtered_df = filtered_df[filtered_df['측정소명'].isin(selected_stations)]

    # 메인 화면
    st.title("🌬️ 2025년 1월 미세먼지 분석 대시보드")
    st.info("GitHub에 업로드된 '202501-air.csv' 데이터를 실시간으로 시각화합니다.")

    # KPI 지표
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("평균 PM10", f"{filtered_df['PM10'].mean():.1f} ㎍/㎥")
    with col2:
        st.metric("평균 PM25", f"{filtered_df['PM25'].mean():.1f} ㎍/㎥")
    with col3:
        st.metric("최고 PM10", f"{filtered_df['PM10'].max():.1f} ㎍/㎥")

    st.divider()

    # 시각화 1: 시간별 변화 추이
    st.subheader("📈 시간별 오염물질 농도 변화")
    pollutant = st.radio("표시 항목 선택", ["PM10", "PM25", "O3", "NO2"], horizontal=True)
    
    fig_line = px.line(
        filtered_df, 
        x='측정일시', 
        y=pollutant, 
        color='측정소명',
        title=f"시간대별 {pollutant} 농도 추이",
        labels={'측정일시': '측정 시간', pollutant: f'{pollutant} (㎍/㎥)'}
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # 시각화 2: 지역별 비교 (Box Plot)
    st.subheader("📊 지역별 농도 분포")
    fig_box = px.box(
        filtered_df, 
        x='시도', 
        y=pollutant, 
        color='시도',
        title=f"시도별 {pollutant} 데이터 분포"
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # 데이터 상세 보기
    with st.expander("원본 데이터 보기"):
        st.dataframe(filtered_df)
else:
    st.warning("데이터를 불러올 수 없습니다. GitHub 저장소에 '202501-air.csv' 파일이 있는지 확인해 주세요.")
