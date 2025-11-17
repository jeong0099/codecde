import streamlit as st
import pandas as pd
from utils.data_loader import load_and_preprocess_data
from typing import Dict, Any, Tuple, Optional, List

# 환경 설정 및 초기화
st.set_page_config(
    page_title="데이터 분석과 시각화를 통한 인구 문제 탐구", 
    layout="wide"
)

# 메인
def main():
    # 데이터 로드
    data, is_data_available, min_year, max_year = load_and_preprocess_data()
    
    data_status = {
        'min_year': min_year,
        'max_year': max_year,
        'is_data_available': is_data_available, 
        'source': "원본 파일",
        'files': data 
    }
    
    # 기존 내용
    st.title("데이터 분석과 시각화를 통한 인구 문제 탐구")
    st.markdown("""
    본 대시보드는 출산율, 인구 구조, 지역별 인구 쏠림 현상 데이터를 분석하는 목적으로 설계되었습니다.
    * CSV 기반으로 시각화하였습니다.
    * 데이터 로드에 실패하면 차트가 표시되지 않습니다.
    * 속도가 느릴 경우 캐시를 삭제해 주세요
    """)

    st.subheader("데이터 로드 상태")
    
    st.info(f"분석 가능 최대 연도 범위: **{data_status['min_year']}년 ~ {data_status['max_year']}년**")

    st.markdown("---")
    st.subheader("파일별 로드 현황")
    
    status_df = pd.DataFrame({
        '데이터셋': ['합계출산율', '총인구/출생/사망', '지역별 인구밀도', '지역별 인구수', '지도 GeoJSON'],
        '필수 파일': ['합계출산율.csv', '인구통계 1998부터.csv', '지역별 인구밀도.csv', '지역별 인구수.csv', 'GeoJSON 파일'],
        '로드 여부': [
            data_status['is_data_available'].get('df_fert', False),
            data_status['is_data_available'].get('df_pop_total', False),
            data_status['is_data_available'].get('df_density', False),
            data_status['is_data_available'].get('df_pop_region', False),
            data_status['is_data_available'].get('korea_geo', False)
        ]
    })
    
    def status_formatter(loaded: bool) -> str:
        return '로드 성공' if loaded else '로드 실패/데이터 부족'
        
    st.table(status_df.style.applymap(lambda x: 'background-color: #fce4e4' if x == '로드 실패/데이터 부족' else ('background-color: #e6ffe6' if x == '로드 성공' else ''), subset=['로드 여부']).format({'로드 여부': status_formatter}))

if __name__ == "__main__":
    main()
