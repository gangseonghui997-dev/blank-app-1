import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="대기질 시각화 대시보드",
    page_icon="🌫️",
    layout="wide"
)

# -----------------------------
# 데이터 로드
# -----------------------------
@st.cache_data
def load_data(file_path: str):
    df = pd.read_csv(file_path)

    # 측정일시 파싱: 예) 2025010101 -> 2025-01-01 01:00
    df["측정일시"] = pd.to_datetime(df["측정일시"].astype(str), format="%Y%m%d%H", errors="coerce")

    # 파생 컬럼
    df["date"] = df["측정일시"].dt.date
    df["hour"] = df["측정일시"].dt.hour

    # 숫자형 처리
    pollutant_cols = ["SO2", "CO", "O3", "NO2", "PM10", "PM25"]
    for col in pollutant_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df

# 파일 경로
FILE_PATH = "202501-air.csv"
df = load_data(FILE_PATH)

st.title("🌫️ 2025년 1월 대기질 시각화 대시보드")
st.caption("업로드된 CSV 파일 기반 Streamlit 대시보드")

# -----------------------------
# 사이드바 필터
# -----------------------------
st.sidebar.header("필터")

region_list = sorted(df["지역"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect(
    "지역 선택",
    options=region_list,
    default=region_list[:5] if len(region_list) >= 5 else region_list
)

filtered_df = df.copy()
if selected_regions:
    filtered_df = filtered_df[filtered_df["지역"].isin(selected_regions)]

station_list = sorted(filtered_df["측정소명"].dropna().unique().tolist())
selected_stations = st.sidebar.multiselect(
    "측정소 선택",
    options=station_list,
    default=station_list[:10] if len(station_list) >= 10 else station_list
)

if selected_stations:
    filtered_df = filtered_df[filtered_df["측정소명"].isin(selected_stations)]

pollutant = st.sidebar.selectbox(
    "오염물질 선택",
    ["PM25", "PM10", "O3", "NO2", "CO", "SO2"],
    index=0
)

date_range = st.sidebar.date_input(
    "날짜 범위 선택",
    value=(filtered_df["date"].min(), filtered_df["date"].max())
)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df["date"] >= start_date) & (filtered_df["date"] <= end_date)
    ]

# 데이터 없을 때
if filtered_df.empty:
    st.warning("선택한 조건에 맞는 데이터가 없습니다.")
    st.stop()

# -----------------------------
# KPI
# -----------------------------
col1, col2, col3, col4 = st.columns(4)

avg_val = filtered_df[pollutant].mean()
max_val = filtered_df[pollutant].max()
min_val = filtered_df[pollutant].min()
obs_count = len(filtered_df)

col1.metric(f"{pollutant} 평균", f"{avg_val:.3f}")
col2.metric(f"{pollutant} 최대", f"{max_val:.3f}")
col3.metric(f"{pollutant} 최소", f"{min_val:.3f}")
col4.metric("측정 건수", f"{obs_count:,}")

st.markdown("---")

# -----------------------------
# 시간대별 평균
# -----------------------------
hourly_df = (
    filtered_df.groupby("hour", as_index=False)[pollutant]
    .mean()
    .sort_values("hour")
)

fig_hour = px.line(
    hourly_df,
    x="hour",
    y=pollutant,
    markers=True,
    title=f"시간대별 평균 {pollutant}"
)
fig_hour.update_layout(
    xaxis_title="시간",
    yaxis_title=f"{pollutant} 평균 농도"
)

# -----------------------------
# 일자별 평균
# -----------------------------
daily_df = (
    filtered_df.groupby("date", as_index=False)[pollutant]
    .mean()
    .sort_values("date")
)

fig_daily = px.line(
    daily_df,
    x="date",
    y=pollutant,
    markers=True,
    title=f"일자별 평균 {pollutant}"
)
fig_daily.update_layout(
    xaxis_title="날짜",
    yaxis_title=f"{pollutant} 평균 농도"
)

left, right = st.columns(2)
with left:
    st.plotly_chart(fig_hour, use_container_width=True)
with right:
    st.plotly_chart(fig_daily, use_container_width=True)

# -----------------------------
# 지역별 평균 비교
# -----------------------------
region_avg_df = (
    filtered_df.groupby("지역", as_index=False)[pollutant]
    .mean()
    .sort_values(pollutant, ascending=False)
)

fig_region = px.bar(
    region_avg_df,
    x="지역",
    y=pollutant,
    title=f"지역별 평균 {pollutant}",
    text_auto=".2f"
)
fig_region.update_layout(
    xaxis_title="지역",
    yaxis_title=f"{pollutant} 평균 농도"
)

st.plotly_chart(fig_region, use_container_width=True)

# -----------------------------
# 측정소별 평균 비교 (상위 20개)
# -----------------------------
station_avg_df = (
    filtered_df.groupby(["지역", "측정소명"], as_index=False)[pollutant]
    .mean()
    .sort_values(pollutant, ascending=False)
    .head(20)
)

station_avg_df["라벨"] = station_avg_df["지역"] + " / " + station_avg_df["측정소명"]

fig_station = px.bar(
    station_avg_df,
    x="라벨",
    y=pollutant,
    title=f"측정소별 평균 {pollutant} 상위 20개",
    text_auto=".2f"
)
fig_station.update_layout(
    xaxis_title="측정소",
    yaxis_title=f"{pollutant} 평균 농도"
)

st.plotly_chart(fig_station, use_container_width=True)

# -----------------------------
# 선택 지역별 추이 비교
# -----------------------------
if len(selected_regions) >= 1:
    region_daily_compare = (
        filtered_df.groupby(["date", "지역"], as_index=False)[pollutant]
        .mean()
        .sort_values("date")
    )

    fig_compare = px.line(
        region_daily_compare,
        x="date",
        y=pollutant,
        color="지역",
        title=f"지역별 일자 추이 비교 - {pollutant}"
    )
    fig_compare.update_layout(
        xaxis_title="날짜",
        yaxis_title=f"{pollutant} 평균 농도"
    )

    st.plotly_chart(fig_compare, use_container_width=True)

# -----------------------------
# 원본 데이터
# -----------------------------
st.subheader("원본 데이터")
show_cols = [
    "지역", "측정소명", "측정일시",
    "SO2", "CO", "O3", "NO2", "PM10", "PM25", "주소"
]
st.dataframe(
    filtered_df[show_cols].sort_values("측정일시"),
    use_container_width=True,
    height=500
)
