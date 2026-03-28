import streamlit as st
from utils.data_loader import load_and_preprocess_data
from utils.plotting import plot_regional_choropleth # 이 모듈 내에 plot_regional_choropleth 함수가 있다고 가정
from typing import Dict, Any, Tuple 

# 데이터 로드
data, is_data_available, min_year_global, max_year_global = load_and_preprocess_data()
MAX_DATA_YEAR = 2024
slider_max_year = min(max_year_global, MAX_DATA_YEAR)


# 필요한 데이터 추출
df_density = data.get('df_density')
df_pop_region = data.get('df_pop_region')
geo_json = data.get('korea_geo')
is_geo_available = is_data_available.get('korea_geo', False)

is_density_available = is_data_available.get('df_density', False)
is_pop_region_available = is_data_available.get('df_pop_region', False)

# 페이지 본문
st.title("지역별 분석")
st.markdown("인구 밀도와 인구수 지도를 통해 지역 불균형 심화 정도를 시각화.")

# 시점 선택
if not (is_density_available or is_pop_region_available):
    st.warning("지역별 지도 분석을 위한 데이터(인구 밀도 또는 인구수)가 로드되지 않았습니다. **(인구 밀도 데이터 로드 상태: {is_density_available}, 인구수 데이터 로드 상태: {is_pop_region_available})**".format(
        is_density_available=is_density_available, 
        is_pop_region_available=is_pop_region_available
    ))
elif not is_geo_available:
    # GeoJSON 로딩 실패 시, GeoJSON 데이터 구조에 대한 디버깅 정보 추가
    st.error("대한민국 GeoJSON 데이터(**korea_geo**)를 로드할 수 없습니다. 지도 렌더링이 불가능합니다.")
    if data.get('korea_geo') is None:
        st.caption("GeoJSON 로드 함수가 None을 반환했습니다. data_loader.py의 파일 경로 또는 원격 URL을 확인하십시오.")
    elif 'features' not in data.get('korea_geo', {}):
        st.caption("GeoJSON 객체는 로드되었으나 'features' 키가 없습니다. GeoJSON 파일 포맷을 확인하십시오.")

else:
    st.subheader("1. 단일 시점 지역별 인구 밀도 및 인구수 지도")
    local_single_year_map: int = st.slider(
        '**[지도 시점]** 분석 연도 선택',
        min_value=min_year_global,
        max_value=MAX_DATA_YEAR, 
        value=slider_max_year, 
        step=1,
        key='regional_map_year'
    )
    st.caption(f"현재 선택된 연도: **{local_single_year_map}년** (데이터 최대 연도: 2024년)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 지역별 인구 밀도")
        if is_density_available and df_density is not None:
            DENSITY_COL_NAME = '인구밀도(명/㎢)'
            if DENSITY_COL_NAME in df_density.columns:
                plot_regional_choropleth(df_density, DENSITY_COL_NAME, local_single_year_map, geo_json, 'density_map', DENSITY_COL_NAME, is_density_available, is_geo_available)
            else:
                st.error(f"데이터프레임에 컬럼 '{DENSITY_COL_NAME}'이(가) 존재하지 않습니다. data_loader.py를 확인하십시오.")
        else:
            st.warning("인구 밀도 데이터(**지역별 인구밀도.csv**)를 로드할 수 없습니다.")


    with col2:
        st.markdown("#### 지역별 인구수")
        if is_pop_region_available and df_pop_region is not None:
            POP_COL_NAME = '인구수(천명)'
            if POP_COL_NAME in df_pop_region.columns:
                plot_regional_choropleth(df_pop_region, POP_COL_NAME, local_single_year_map, geo_json, 'population_map', POP_COL_NAME, is_pop_region_available, is_geo_available)
            else:
                st.error(f"데이터프레임에 컬럼 '{POP_COL_NAME}'이(가) 존재하지 않습니다. data_loader.py를 확인하십시오.")
        else:
            st.warning("지역별 인구수 데이터(**지역별 인구수.csv**)를 로드할 수 없습니다.")
