import streamlit as st
import pandas as pd
from utils.data_loader import load_and_preprocess_data
from utils.plotting import plot_fertility_and_prediction, plot_birth_death_crossover
from typing import Dict, Any, Tuple

# 데이터 로드
data, is_data_available, min_year_global, max_year_global = load_and_preprocess_data()

# 필요한 데이터 추출
df_fert = data.get('df_fert')
df_pop_total = data.get('df_pop_total')

is_fert_available = is_data_available.get('df_fert', False)
is_pop_total_available = is_data_available.get('df_pop_total', False)

# 페이지 본문
st.title("출산율 관련 데이터 분석")
st.markdown("출산율 동향과 출생/사망 추이를 시각화하여 분석.")

# 합계출산율 동향
st.subheader("1. 연도별 합계출산율 동향 및 예측")
if is_fert_available and df_fert is not None:
    local_range_fert: Tuple[int, int] = st.slider(
        '분석 기간 선택',
        min_value=min_year_global,
        max_value=2029,
        value=(max(min_year_global, 2000), min(max_year_global, 2029)),
        step=1,
        key='fertility_trend_range'
    )

    fert_col = "합계출산율" if "합계출산율" in df_fert.columns else None
    st.write("선택된 출산율 컬럼:", fert_col)

    if fert_col:
        try:
            plot_fertility_and_prediction(df_fert, fert_col, local_range_fert, is_fert_available)
            st.markdown("※ 향후 예측값은 회귀분석 결과임.")
        except Exception as e:
            st.error(f"그래프 렌더링 중 오류 발생: {e}")
    else:
        st.warning("'합계출산율' 컬럼을 찾을 수 없습니다. CSV 구조를 확인하세요.")
else:
    st.warning("합계출산율 데이터를 로드할 수 없습니다. '합계출산율.csv' 파일을 확인하세요.")

# 출생/사망자수 추이
st.subheader("2. 출생자수/사망자수 추이 분석")
if is_pop_total_available and df_pop_total is not None:
    local_range_bd: Tuple[int, int] = st.slider(
        '**[출생/사망]** 분석 기간 선택',
        min_value=min_year_global,
        max_value=2024,
        value=(max(min_year_global, 1999), min(max_year_global, 2024)),
        step=1,
        key='birth_death_trend_range'
    )

    birth_col = next((c for c in df_pop_total.columns if "출생자수" in str(c)), None)
    death_col = next((c for c in df_pop_total.columns if "사망자수" in str(c)), None)

    if birth_col and death_col:
        plot_birth_death_crossover(df_pop_total, birth_col, death_col, local_range_bd, is_pop_total_available)
    else:
        st.warning("'출생자수' 또는 '사망자수' 컬럼을 찾을 수 없습니다. 인구통계 CSV 구조를 확인하세요.")
else:
    st.warning("인구통계 데이터를 로드할 수 없습니다. '인구통계 1998부터.csv' 파일을 확인하세요.")
