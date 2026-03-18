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

# Custom Styling
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        color: #1f3b4d;
    }
</style>
""", unsafe_allow_html=True)

# Data Loading Cache
@st.cache_data
def load_data(file_path):
    df = pd.read_csv(file_path)
    
    # Preprocessing Date/Time
    # 측정일시: 2025010101 format (YYYYMMDDHH)
    # 24 is handled by mapping it to 00 and adding one day (or just treating it as hour 23+1)
    # Simple fix for hour 24:
    def parse_hour_24(dt_str):
        date_part = str(dt_str)[:8]
        hour_part = str(dt_str)[8:]
        if hour_part == '24':
            dt = datetime.strptime(date_part, '%Y%m%d')
            return dt + pd.Timedelta(days=1)
        else:
            return datetime.strptime(str(dt_str), '%Y%m%d%H')

    df['측정일시_dt'] = df['측정일시'].apply(parse_hour_24)
    
    # Numeric columns conversion
    pollutants = ['SO2', 'CO', 'O3', 'NO2', 'PM10', 'PM25']
    for p in pollutants:
        df[p] = pd.to_numeric(df[p], errors='coerce')
    
    return df

# Initialize session state for better experience
if 'data' not in st.session_state:
    try:
        st.session_state.data = load_data(r'C:\anti\0318_3\202501-air.csv')
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        st.stop()

df = st.session_state.data

# Sidebar Navigation
st.sidebar.title("🔍 검색 필터")

# 1. Select Region (지역)
regions = sorted(df['지역'].unique())
selected_region = st.sidebar.selectbox("지역 선택", regions)

# Filter by selected region
df_region = df[df['지역'] == selected_region]

# 2. Select Station Name (측정소명)
stations = sorted(df_region['측정소명'].unique())
selected_station = st.sidebar.selectbox("측정소 선택", stations)

# 3. Select Pollutant
pollutant_options = {
    'PM10': '미세먼지 (PM10)',
    'PM25': '초미세먼지 (PM2.5)',
    'O3': '오존 (O3)',
    'NO2': '이산화질소 (NO2)',
    'CO': '일산화탄소 (CO)',
    'SO2': '아황산가스 (SO2)'
}
selected_p_code = st.sidebar.selectbox("대기오염물질 선택", options=list(pollutant_options.keys()), format_func=lambda x: pollutant_options[x])

# 4. Date Range
min_date = df['측정일시_dt'].min().date()
max_date = df['측정일시_dt'].max().date()
start_date, end_date = st.sidebar.date_input("조회 기간", [min_date, max_date], min_value=min_date, max_value=max_date)

# Apply filters to main data
mask = (df_region['측정소명'] == selected_station) & \
       (df_region['측정일시_dt'].dt.date >= start_date) & \
       (df_region['측정일시_dt'].dt.date <= end_date)
df_filtered = df_region.loc[mask].sort_values('측정일시_dt')

# --- Main Dashboard ---
st.title("🌬️ 대기질 데이터 시각화 대시보드")
st.markdown(f"**조회 대상:** {selected_region} > {selected_station} | **기간:** {start_date} ~ {end_date}")

# 1. Summary Metrics
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

# 2. Time Series Chart
st.divider()
st.subheader(f"📈 {pollutant_options[selected_p_code]} 농도 추이")

fig_line = px.line(df_filtered, x='측정일시_dt', y=selected_p_code, 
                  labels={'측정일시_dt': '날짜/시간', selected_p_code: pollutant_options[selected_p_code]},
                  template="plotly_white", color_discrete_sequence=['#4B8BBE'])
fig_line.update_layout(hovermode="x unified")
st.plotly_chart(fig_line, use_container_width=True)

# 3. Regional Comparison
st.divider()
st.subheader(f"🏢 {selected_region} 내 다른 측정소와 비교 (기간 평균)")

# Calculate regional station averages
regional_avgs = df_region[(df_region['측정일시_dt'].dt.date >= start_date) & 
                         (df_region['측정일시_dt'].dt.date <= end_date)] \
                .groupby('측정소명')[selected_p_code].mean().reset_index()

fig_bar = px.bar(regional_avgs.sort_values(selected_p_code), x=selected_p_code, y='측정소명',
                labels={selected_p_code: f'평균 {pollutant_options[selected_p_code]}'},
                orientation='h', template="plotly_white", color=selected_p_code,
                color_continuous_scale='Viridis')
st.plotly_chart(fig_bar, use_container_width=True)

# 4. Data Table
st.divider()
with st.expander("📄 상세 데이터 보기"):
    st.dataframe(df_filtered[['측정일시_dt', '측정소명', 'SO2', 'CO', 'O3', 'NO2', 'PM10', 'PM25', '주소']], use_container_width=True)

st.sidebar.info(f"데이터 파일: 202501-air.csv\n전체 행 수: {len(df):,}")
