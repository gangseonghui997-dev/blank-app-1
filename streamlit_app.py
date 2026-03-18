import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="2025년 1월 대기질분석 대시보드",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 데이터 로딩 및 캐싱
@st.cache_data
def load_air_data(file_path):
    df = pd.read_csv(file_path)
    
    # 시간 파싱 (24시 처리 포함)
    def parse_hour_24(dt_str):
        dt_str = str(dt_str)
        date_part = dt_str[:8]
        hour_part = dt_str[8:]
        try:
            if hour_part == '24':
                dt = datetime.strptime(date_part, '%Y%m%d')
                return dt + pd.Timedelta(days=1)
            else:
                return datetime.strptime(dt_str, '%Y%m%d%H')
        except:
            return pd.NaT

    df['날짜시간'] = df['측정일시'].apply(parse_hour_24)
    df['날짜'] = df['날짜시간'].dt.date
    
    # 수치형 변환
    pollutants = ['SO2', 'CO', 'O3', 'NO2', 'PM10', 'PM25']
    for p in pollutants:
        df[p] = pd.to_numeric(df[p], errors='coerce')
    
    return df

# 데이터 로드 시도
try:
    import os
    # 스크립트 파일의 위치를 기준으로 CSV 파일 경로 설정 (가장 확실한 방법)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, '202501-air.csv')
    
    # 만약 파일이 없으면 원래 보여주던 경로도 확인 시도
    if not os.path.exists(file_path):
        file_path = r'C:\anti\0318_3\202501-air.csv'
        
    df = load_air_data(file_path)
except Exception as e:
    import os
    st.error(f"데이터 로드 실패: {e}")
    st.write(f"현재 실행 경로 (CWD): {os.getcwd()}")
    st.write(f"스크립트 위치: {os.path.dirname(os.path.abspath(__file__))}")
    st.stop()

# 3. 사이드바 구성
with st.sidebar:
    st.header("⚙️ 대시보드 제어판")
    st.caption("필터를 조정하여 데이터를 탐색하세요.")
    
    # 지역 필터
    all_regions = sorted(df['지역'].unique())
    selected_regions = st.multiselect(
        "분석 지역 선택",
        options=all_regions,
        default=all_regions[:3] if len(all_regions) > 3 else all_regions
    )
    
    # 측정소 필터 (지역에 종속)
    available_stations = sorted(df[df['지역'].isin(selected_regions)]['측정소명'].unique())
    selected_stations = st.multiselect(
        "측정소 선택",
        options=available_stations,
        default=available_stations[:1] if available_stations else []
    )
    
    # 날짜 범위 필터
    min_date = df['날짜'].min()
    max_date = df['날짜'].max()
    date_range = st.date_input(
        "조회 기간",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    st.divider()
    
    if st.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

# 조회 기간 예외 처리
if isinstance(date_range, list) or isinstance(date_range, tuple):
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0]
else:
    start_date = end_date = date_range

# 필터링 적용
filtered_df = df[
    (df['지역'].isin(selected_regions)) &
    (df['측정소명'].isin(selected_stations)) &
    (df['날짜'] >= start_date) &
    (df['날짜'] <= end_date)
].sort_values('날짜시간')

# 4. 메인 레이아웃 및 헤더
st.title("🌬️ 대기환경 모니터링 대시보드 (2025-01)")
st.markdown(f"**분석 범위:** {', '.join(selected_regions)} 지역 | {len(selected_stations)}개 측정소")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["📊 주요 오염원 분석", "📋 상세 데이터 내역", "💡 사용 가이드"])

with tab1:
    # 5. 핵심 지표 (Metrics)
    col1, col2, col3, col4 = st.columns(4)
    
    if not filtered_df.empty:
        p_latest = filtered_df.iloc[-1]
        pm10_avg = filtered_df['PM10'].mean()
        pm25_avg = filtered_df['PM25'].mean()
        o3_avg = filtered_df['O3'].mean()
        
        with col1:
            st.metric(label="PM10 평균", value=f"{pm10_avg:.1f} ㎍/㎥", delta=f"{pm10_avg - 40:.1f}", delta_color="inverse")
        with col2:
            st.metric(label="PM2.5 평균", value=f"{pm25_avg:.1f} ㎍/㎥", delta=f"{pm25_avg - 15:.1f}", delta_color="inverse")
        with col3:
            st.metric(label="오존(O3) 평균", value=f"{o3_avg:.3f} ppm", delta=f"{o3_avg - 0.03:.3f}", delta_color="inverse")
        with col4:
            st.metric(label="데이터 건수", value=f"{len(filtered_df):,}건")
    else:
        st.warning("선택된 조건에 해당하는 데이터가 없습니다.")

    st.divider()

    # 6. 차트 분석
    chart_col1, chart_col2 = st.columns([2, 1])
    
    with chart_col1:
        st.subheader("시간별 미세먼지(PM10) 추이")
        fig_pm10 = px.line(
            filtered_df, x='날짜시간', y='PM10', color='측정소명',
            template='plotly_white', title="PM10 Concentration Over Time"
        )
        st.plotly_chart(fig_pm10, use_container_width=True)

    with chart_col2:
        st.subheader("오염물질 간 상관관계 (PM10 vs PM2.5)")
        fig_scatter = px.scatter(
            filtered_df, x='PM10', y='PM25', color='측정소명',
            template='plotly_white', opacity=0.5
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.divider()
    
    # 지역별 평균 비교
    st.subheader("지역별 주요 오염물질 평균 농도 비교")
    regional_avg = df[
        (df['날짜'] >= start_date) & (df['날짜'] <= end_date)
    ].groupby('지역')[['PM10', 'PM25', 'O3', 'NO2']].mean().reset_index()
    
    fig_bar = px.bar(
        regional_avg.melt(id_vars='지역', var_name='오염물질', value_name='농도'),
        x='지역', y='농도', color='오염물질', barmode='group',
        template='plotly_white'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    st.subheader("측정 결과 데이터셋")
    
    # 7. 데이터프레임 스타일링
    st.dataframe(
        filtered_df.style.highlight_max(subset=['PM10', 'PM25'], color='lightpink')
                    .highlight_min(subset=['PM10', 'PM25'], color='lightblue'),
        use_container_width=True,
        hide_index=True
    )
    
    # 다운로드 버튼
    csv = filtered_df.to_csv(index=False).encode('utf-8-sig') # 한글 깨짐 방지 utf-8-sig
    st.download_button(
        label="📥 필터링된 데이터 CSV 다운로드",
        data=csv,
        file_name='air_quality_filtered_data.csv',
        mime='text/csv'
    )

with tab3:
    st.subheader("대시보드 안내")
    with st.expander("📌 분석 항목 및 기준 안내"):
        st.markdown("""
        * **PM10 (미세먼지):** 입자의 크기가 10㎛ 이하인 먼지. (환경기준: 일평균 100㎍/㎥ 이하)
        * **PM2.5 (초미세먼지):** 입자의 크기가 2.5㎛ 이하인 먼지. (환경기준: 일평균 35㎍/㎥ 이하)
        * **O3 (오존):** 대기 중 질소산화물과 휘발성 유기화합물이 태양광선과 반응하여 생성.
        * **데이터 출처:** 국가대기오염정보관리시스템 (AirKorea) 2025년 1월 데이터
        """)
    
    st.info("좌측 사이드바에서 여러 지역과 측정소를 동시에 선택하여 비교 분석할 수 있습니다.")
