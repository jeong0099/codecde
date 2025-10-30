import streamlit as st
import pandas as pd
import os
import re
from typing import Dict, Any, Tuple, Optional, List
import json as json_lib

ROOT_CANDIDATES = ["./", "/mnt/data/"]

def find_file_any(name_variants: List[str]) -> Optional[str]:
    for root in ROOT_CANDIDATES:
        for v in name_variants:
            p = os.path.join(root, v)
            if os.path.exists(p):
                return p
    return None

def preprocess_wide_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.set_index(df.columns[0]).T
    df = df.reset_index().rename(columns={'index': '연도'})
    df['연도'] = pd.to_numeric(df['연도'], errors='coerce')
    for col in df.columns[1:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def try_read_csv(path: Optional[str]) -> Optional[pd.DataFrame]:
    if path is None or not os.path.exists(path):
        return None

    try:
        df = pd.read_csv(path, encoding='utf-8-sig')

        # Transposed Wide Format
        if df.columns[0] == '연도':
            numeric_cols = [c for c in df.columns[1:] if re.match(r'^\d{4}$', str(c))]
            if len(numeric_cols) >= 10:
                return preprocess_wide_data(df)

        # General Wide Format
        if df.shape[1] >= 10:
            first_col = df.columns[0]
            if '연도' in first_col or 'year' in first_col.lower() or 'index' in first_col.lower():
                return preprocess_wide_data(df)

        return df

    except Exception as e:
        print(f"CSV 로딩 실패: {path}, 오류: {e}")
        return None

@st.cache_data
def load_korea_geo_json() -> Optional[Dict[str, Any]]:
    geojson_local = find_file_any(["korea_geojson.json"])
    if geojson_local:
        try:
            with open(geojson_local, "rb") as f:
                raw_bytes = f.read()
                return json_lib.loads(raw_bytes.decode('utf-8'))
        except Exception as e:
            print(f"Error loading GeoJSON: {e}")
    return None

@st.cache_data
def load_and_preprocess_data() -> Tuple[Dict[str, Optional[pd.DataFrame]], Dict[str, bool], int, int]:
    # 강제 전처리
    fert_path = find_file_any(["합계출산율.csv"])
    pop_path = find_file_any(["인구통계 1998부터.csv", "인구수 1970년부터.csv"])

    data_raw = {
        'df_fert_raw': preprocess_wide_data(pd.read_csv(fert_path, encoding='utf-8-sig')) if fert_path else None,
        'df_pop_total_raw': preprocess_wide_data(pd.read_csv(pop_path, encoding='utf-8-sig')) if pop_path else None,
        'df_age_sex_raw': try_read_csv(find_file_any(["성연령통계.csv", "성_연령별_인구.csv", "성연령계.csv"])),
        'df_age_wide_raw': try_read_csv(find_file_any(["연령별인구통계.csv", "연령별 인구구조.csv"])),
        'df_density_raw': try_read_csv(find_file_any(["지역별 인구밀도.csv"])),
        'df_pop_region_raw': try_read_csv(find_file_any(["지역별 인구수.csv"])),
    }

    data: Dict[str, Optional[pd.DataFrame]] = {}
    is_data_available: Dict[str, bool] = {}

    region_name_map = {
        "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시", "인천": "인천광역시",
        "광주": "광주광역시", "대전": "대전광역시", "울산": "울산광역시", "세종": "세종특별자치시",
        "경기": "경기도", "강원": "강원특별자치도", "충북": "충청북도", "충남": "충청남도",
        "전북": "전라북도", "전남": "전라남도", "경북": "경상북도", "경남": "경상남도",
        "제주": "제주특별자치도"
    }

    # 연령별 인구
    if data_raw.get('df_age_wide_raw') is not None and not data_raw['df_age_wide_raw'].empty:
        df_age_wide = data_raw['df_age_wide_raw']
        age_cols = [c for c in df_age_wide.columns if c != '연도' and pd.api.types.is_numeric_dtype(df_age_wide[c])]
        df_age_long_temp = df_age_wide.melt(id_vars='연도', value_vars=age_cols, var_name='연령대', value_name='인구수')
        data['df_age_long'] = df_age_long_temp.dropna(subset=['연도', '인구수'])
        data['df_age_wide'] = df_age_wide
        is_data_available['df_age_long'] = True
        is_data_available['df_age_wide'] = True
    else:
        data['df_age_long_sex'] = None

    # 출산율, 전체 인구
    data['df_fert'] = data_raw.get('df_fert_raw')
    data['df_pop_total'] = data_raw.get('df_pop_total_raw')
    is_data_available['df_fert'] = data['df_fert'] is not None and not data['df_fert'].empty
    is_data_available['df_pop_total'] = data['df_pop_total'] is not None and not data['df_pop_total'].empty

    # 인구밀도
    if data_raw.get('df_density_raw') is not None and not data_raw['df_density_raw'].empty:
        df_density = data_raw['df_density_raw']
        df_density_long = df_density.melt(id_vars='연도', var_name='지역', value_name='인구밀도(명/㎢)')
        df_density_long['지역'] = df_density_long['지역'].map(region_name_map)
        data['df_density'] = df_density_long
        is_data_available['df_density'] = not df_density_long.empty
    else:
        data['df_density'] = None
        is_data_available['df_density'] = False

    # 인구수
    if data_raw.get('df_pop_region_raw') is not None and not data_raw['df_pop_region_raw'].empty:
        df_pop_region = data_raw['df_pop_region_raw']
        df_pop_region_long = df_pop_region.melt(id_vars='연도', var_name='지역', value_name='인구수(천명)')
        df_pop_region_long['지역'] = df_pop_region_long['지역'].map(region_name_map)
        data['df_pop_region'] = df_pop_region_long
        is_data_available['df_pop_region'] = not df_pop_region_long.empty
    else:
        data['df_pop_region'] = None
        is_data_available['df_pop_region'] = False

    # GeoJSON
    data['korea_geo'] = load_korea_geo_json()
    is_data_available['korea_geo'] = data['korea_geo'] is not None

    # 연도 범위
    years: List[int] = []
    for df in data.values():
        if isinstance(df, pd.DataFrame) and '연도' in df.columns:
            years.extend(df['연도'].dropna().astype(int).unique().tolist())

    min_year = int(min(years)) if years else 1970
    max_year = int(max(years)) if years else 2024

    return data, is_data_available, min_year, max_year