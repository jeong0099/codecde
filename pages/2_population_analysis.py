import streamlit as st
import pandas as pd
import re
from utils.data_loader import load_and_preprocess_data
from utils.plotting import plot_population_pyramid, plot_age_trend, plot_age_structure_comparison, plot_age_trend_bar
from typing import Dict, Any, Tuple, List

# 데이터 로드
data, is_data_available, min_year_global, max_year_global = load_and_preprocess_data()

# 필요한 데이터 추출
df_age_long = data.get('df_age_long')
is_age_data_available = is_data_available.get('df_age_long', False)
df_age_long_sex = data.get('df_age_long_sex') # 현재는 사용하지 않음

# 페이지 본문
st.title("인구 구조 분석")
st.markdown("특정 시점의 연령 분포, 연령대별 총 인구 추이, 두 시점의 연령대별 인구 구조를 시각화하였다.")
st.markdown("시간이 지날 수록 청년층 비율은 감소하고 노년층 비율이 늘어나는 것을 확인할 수 있다.")

if not is_age_data_available or df_age_long is None:
    st.warning("인구 구조 분석을 위한 데이터(**성연령통계.csv** 또는 **연령별인구통계.csv**)가 로드되지 않았거나 데이터 형식이 올바르지 않습니다.")
else:
    # 연령대 정보 추출 및 정렬
    def age_sort_key(age_str: str) -> int:
        match = re.search(r'\d+', str(age_str))
        return int(match.group(0)) if match else 0
        
    age_groups: List[str] = sorted(df_age_long['연령대'].unique().tolist(), key=age_sort_key)
    
    if not age_groups:
        st.warning("연령대 정보(컬럼)를 찾을 수 없습니다.")
        st.stop() # 연령대 정보 없으면 스크립트 실행 중단
    
    min_age_idx = 0
    max_age_idx = len(age_groups) - 1

    # 1. 시기별 연령 분포 통계
    st.subheader("1. 시기별 연령 분포 통계")

    local_single_year: int = st.slider(
        '**[분석 시점]** 연령 분포 분석 연도 선택',
        min_value=min_year_global,
        max_value=max_year_global,
        value=2022,
        step=1,
        key='age_snapshot_year'
    )
    
    st.markdown("#### 연령대별 총 인구 분포")
    plot_population_pyramid(df_age_long, local_single_year, is_age_data_available)
    st.markdown("90년대의 경우 청년층, 20년대의 경우 중년층, 30년대부터 노년층 인구의 비율이 높아지는 경향을 보임.")
        
    
    # 연령대별 총 인구 추이
    st.subheader("2. 주요 연령대별 총 인구수 변화 추이")
    local_range_age_trend: Tuple[int, int] = st.slider(
        '**[연령대별 추이]** 분석 기간 선택',
        min_value=min_year_global,
        max_value=max_year_global,
        value=(max(min_year_global, 1970), max_year_global),
        step=1,
        key='age_trend_range'
    )
    
    # 선 그래프
    plot_age_trend(df_age_long, local_range_age_trend, is_age_data_available)

    # 막대 그래프
    st.markdown("#### 연령대별 총 인구수 변화 추이 (막대 그래프)")
    plot_age_trend_bar(df_age_long, local_range_age_trend, is_age_data_available)


    # 연령별 인구 구조 비교
    st.subheader("3. 두 시점의 연령 구조 비교 분석")
    
    col_y, col_a = st.columns(2)
    
    with col_y:
        local_range_comparison: Tuple[int, int] = st.slider(
            '**① 비교 대상 연도 선택**',
            min_value=min_year_global,
            max_value=max_year_global,
            value=(max(min_year_global, 2022), max_year_global), 
            step=1,
            key='age_comparison_year_range'
        )
    with col_a:
        initial_min_age = age_groups[min_age_idx]
        initial_max_age = age_groups[max_age_idx]

        st.select_slider(
            '**② 비교 대상 연령대 선택**',
            options=age_groups, 
            value=(initial_min_age, initial_max_age), 
            key='age_comparison_age_range'
        )

    plot_age_structure_comparison(
        df_age_long, 
        local_range_comparison, 
        age_groups, 
        is_age_data_available
    )
st.markdown("1970년과 100년 후인 2070년은 서로 상반된 결과를 보임.")
