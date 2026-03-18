import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="대기질 데이터 대시보드 (2025-01)",
    page_icon="🌬️",
    layout="wide"
)

# Data Loading
@st.cache_data
def load_data(file_path):
    try:
        df = pd.read_csv(file_path, encoding="cp949")
    except:
        df = pd.read_csv(file_path, encoding="utf-8")

    # Parse date
    def parse_hour_24(dt_str):
        date_part = str(dt_str)[:8]
        hour_part = str(dt_str)[8:]
        if hour_part == '24':
            dt = datetime.strptime(date_part, '%Y%m%d')
            return dt + pd.Timedelta(days=1)
        else:
            return datetime.strptime(str(dt_str), '%Y%m%d%H')

    df['측정일시_dt'] = df['측정일시'].apply(parse_hour_24)

    pollutants = ['SO2', 'CO', 'O3', 'NO2', 'PM10', 'PM25']
    for p in pollutants:
        df[p] = pd.to_numeric(df[p], errors='coerce')

    return df


# -----------------------------
# 1) CSV 파일 로딩 방식 개선
# -----------------------------
st.sidebar.header("📁 데이터 파일 선택")

uploaded_file = st.sidebar.file_uploader("CSV 파일 업로드", type=["csv"])

if uploaded_file:
    df = load_data(uploaded_file)
else:
    # GitHub RAW URL 직접 읽기
    default_url = "https://raw.githubusercontent.com/gangseonghui997-dev/blank-app-1/main/202501-air.csv"
    try:
        df = load_data(default_url)
        st.sidebar.success("GitHub에서 기본 CSV 파일을 불러왔습니다.")
    except Exception as e:
        st.error("CSV 파일을 불러올 수 없습니다. 파일을 업로드해주세요.")
        st.stop()


# Sidebar Navigation
st.sidebar.title("🔍 검색 필터")

regions = sorted(df['지역'].unique())
selected_region = st.sidebar.selectbox("지역 선택", regions)

df_region = df[df['지역'] == selected_region]

stations = sorted(df_region['측정소명'].unique())
selected_station = st.sidebar.selectbox("측정소 선택", stations)

pollutant_options = {
    'PM10': '미세먼지 (PM10)',
    'PM25': '초미세먼지 (PM2.5)',
    'O3': '오존 (O3)',
    'NO2': '이산화질소 (NO2)',
    'CO': '일산화탄소 (CO)',
    'SO2': '아황산가스 (SO2)'
}
selected_p_code = st.sidebar.selectbox("대기오염물질 선택", options=list(pollutant_options.keys()),
                                       format_func=lambda x: pollutant_options[x])

min_date = df['측정일시_dt'].min().date()
max_date = df['측정일시_dt'].max().date()
start_date, end_date = st.sidebar.date_input("조회 기간", [min_date, max_date],
                                             min_value=min_date, max_value=max_date)

mask = (df_region['측정소명'] == selected_station) & \
       (df_region['측정일시_dt'].dt.date >= start_date) & \
       (df_region['측정일시_dt'].dt.date <= end_date)

df_filtered = df_region.loc[mask].sort_values('측정일시_dt')

# Main Dashboard
st.title("🌬️ 대기질 데이터 시각화 대시보드")
st.markdown(f"**조회 대상:** {selected_region} > {selected_station} | **기간:** {start_date} ~ {end_date}")

# Summary Metrics
st.subheader("📊 주요 통계")
col1, col2, col3, col4 = st.columns(4)

current_val = df_filtered[selected_p_code].iloc[-1] if not df_filtered.empty else 0
avg_val = df_filtered[selected_p_code].mean()
max_val = df_filtered[selected_p_code].max()
min_val = df_filtered[selected_p_code].min()

col1.metric("최근 측정값", f"{current_val:.4g}")
col2.metric("평균값", f"{avg_val:.4g}")
col3.metric("최대값", f"{max_val:.4g}")
col4.metric("최소값", f"{min_val:.4g}")

# Time Series Chart
st.divider()
st.subheader(f"📈 {pollutant_options[selected_p_code]} 농도 추이")

fig_line = px.line(df_filtered, x='측정일시_dt', y=selected_p_code,
                   labels={'측정일시_dt': '날짜/시간', selected_p_code: pollutant_options[selected_p_code]},
                   template="plotly_white", color_discrete_sequence=['#4B8BBE'])
fig_line.update_layout(hovermode="x unified")
st.plotly_chart(fig_line, use_container_width=True)

# Regional Comparison
st.divider()
st.subheader
