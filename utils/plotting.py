import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression 
import re 
from typing import Dict, Any, Tuple, Optional, List

def set_plotly_default(fig: go.Figure, title: Optional[str] = None) -> go.Figure:
    if title:
        fig.update_layout(title_text=f"<b>{title}</b>", title_x=0.5)
    
    fig.update_layout(
        font=dict(family="Noto Sans KR, sans-serif", size=11), 
        hovermode="x unified",
        margin=dict(t=50, b=20, l=20, r=20),
        xaxis_title=None,
        yaxis_title=None
    )
    fig.update_xaxes(showgrid=False)
    return fig


def plot_fertility_and_prediction(df_fert: pd.DataFrame, fert_col: str, local_range: Tuple[int, int], is_data_available: bool):
    if not is_data_available or fert_col is None:
        return
        
    local_start, local_end = local_range
    filtered_fert = df_fert.query('연도 >= @local_start & 연도 <= @local_end').copy()
    train_df = filtered_fert.dropna(subset=['연도', fert_col])
    
    if train_df.empty:
        return 

    if len(train_df) >= 2:
        model = LinearRegression()
        X = train_df['연도'].values.reshape(-1, 1)
        y = train_df[fert_col].values
        
        try:
            model.fit(X, y)
        except ValueError:
            plot_pred = train_df.copy(); plot_pred['유형'] = '실제 출산율'
        else:
            # 향후 5년 예측
            max_year_data = train_df['연도'].max()
            future_years = np.arange(max_year_data + 1, max_year_data + 6).reshape(-1, 1)
            predictions = model.predict(future_years)
            pred_df = pd.DataFrame({'연도': future_years.flatten(), fert_col: predictions.round(3)})
            plot_pred = pd.concat([train_df, pred_df])
            plot_pred['유형'] = ['실제 출산율'] * len(train_df) + ['향후 예측 (선형)'] * len(pred_df)
    else:
        plot_pred = train_df.copy(); plot_pred['유형'] = '실제 출산율'

    fig = px.line(plot_pred, x="연도", y=fert_col, color="유형", 
                    title=f"합계출산율 추이 및 향후 예측 ({local_start}년 ~ {local_end}년)",
                    markers=True,
                    color_discrete_map={'실제 출산율': '#3498DB', '향후 예측 (선형)': '#E74C3C'})
    
    fig.add_hline(y=0.7, line_width=1, line_dash="dash", line_color="orange", annotation_text="초저출산 기준 (0.7)", annotation_position="top left")
    st.plotly_chart(set_plotly_default(fig), use_container_width=True)


def plot_birth_death_crossover(df_pop_total: pd.DataFrame, birth_col: str, death_col: str, local_range: Tuple[int, int], is_data_available: bool):
    if not is_data_available or birth_col is None or death_col is None:
        return

    local_start, local_end = local_range
    filtered_pop_total = df_pop_total.query('연도 >= @local_start & 연도 <= @local_end')
    
    if filtered_pop_total.empty:
        return

    bd_df = filtered_pop_total[['연도', birth_col, death_col]].melt(id_vars='연도', var_name='구분', value_name='인구수')
    
    fig = px.line(bd_df, x='연도', y='인구수', color='구분', 
                      title=f"출생자수 및 사망자수 추이 ({local_start}년 ~ {local_end}년)",
                      color_discrete_map={birth_col: '#2ECC71', death_col: '#E74C3C'})
    
    dead_cross_data = filtered_pop_total[filtered_pop_total[death_col] > filtered_pop_total[birth_col]]
    dead_cross_year = dead_cross_data['연도'].min()
    
    if not pd.isna(dead_cross_year):
        fig.add_vline(x=dead_cross_year, line_width=1, line_dash="dash", line_color="#7F8C8D", 
                          annotation_text=f"데드크로스 ({int(dead_cross_year)}년)", 
                          annotation_position="bottom right",
                          annotation_font_color="#7F8C8D")
                          
    fig.update_yaxes(tickformat=',.0f')
    st.plotly_chart(set_plotly_default(fig), use_container_width=True)


def plot_population_pyramid(df_age_long: pd.DataFrame, local_year: int, is_data_available: bool):
    if not is_data_available:
        return
        
    plot_age_snap = df_age_long[df_age_long['연도'] == local_year].copy()
    
    if plot_age_snap.empty or '인구수' not in plot_age_snap.columns or not pd.api.types.is_numeric_dtype(plot_age_snap['인구수']):
        return

    # 연령대 정렬 순서 정의
    def age_sort_key(age_str: str) -> int:
        match = re.search(r'\d+', str(age_str))
        return int(match.group(0)) if match else 0
        
    age_order = sorted(plot_age_snap['연령대'].unique().tolist(), key=age_sort_key) 
    
    plot_age_snap['연령대'] = pd.Categorical(plot_age_snap['연령대'], categories=age_order, ordered=True)
    plot_age_snap = plot_age_snap.sort_values('연령대')

    fig = px.bar(plot_age_snap, x='연령대', y='인구수', color='연령대', 
                      title=f"<b>{local_year}년</b> 연령대별 총 인구 분포",
                      category_orders={"연령대": age_order})
    fig.update_yaxes(tickformat=',.0f')
    st.plotly_chart(set_plotly_default(fig), use_container_width=True)

    
def plot_age_trend(df_age_long: pd.DataFrame, local_range: Tuple[int, int], is_data_available: bool):
    if not is_data_available:
        return

    local_start, local_end = local_range
    filtered_age_trend = df_age_long.query('연도 >= @local_start & 연도 <= @local_end')
    
    if filtered_age_trend.empty:
        return
        
    fig = px.line(filtered_age_trend, x='연도', y='인구수', color='연령대', 
                      title=f"주요 연령대별 총 인구수 변화 추이 ({local_start}년 ~ {local_end}년)")
    fig.update_yaxes(tickformat=',.0f')
    st.plotly_chart(set_plotly_default(fig), use_container_width=True)

def plot_age_trend_bar(df_age_long: pd.DataFrame, local_range: Tuple[int, int], is_data_available: bool):
    if not is_data_available:
        return

    local_start, local_end = local_range
    filtered_age_trend = df_age_long.query('연도 >= @local_start & 연도 <= @local_end')
    
    if filtered_age_trend.empty:
        return
        
    # 막대 차트를 그룹 모드로 설정
    fig = px.bar(filtered_age_trend, x='연도', y='인구수', color='연령대', 
                      title=f"주요 연령대별 총 인구수 변화 추이 (막대 차트) ({local_start}년 ~ {local_end}년)",
                      barmode='group')
    
    # x축을 정수형 연도
    fig.update_xaxes(tickmode='linear', dtick=5, tick0=local_start)
    fig.update_yaxes(tickformat=',.0f')
    st.plotly_chart(set_plotly_default(fig), use_container_width=True)


def plot_age_structure_comparison(df_age_long: pd.DataFrame, local_range: Tuple[int, int], age_groups: List[str], is_data_available: bool):
    if not is_data_available:
        return
    
    start_year, end_year = local_range
    
    if 'age_comparison_age_range' in st.session_state:
        start_age_str, end_age_str = st.session_state['age_comparison_age_range']
    else:
        start_age_str, end_age_str = age_groups[0], age_groups[-1]


    try:
        start_idx = age_groups.index(start_age_str)
        end_idx = age_groups.index(end_age_str)
        selected_age_groups = age_groups[start_idx : end_idx + 1]
    except ValueError:
        return

    # 두 연도 및 선택된 연령대
    df_filtered = df_age_long[
        (df_age_long['연도'].isin([start_year, end_year])) &
        (df_age_long['연령대'].isin(selected_age_groups))
    ] 
    
    if df_filtered.empty:
        return

    # 연령대 정렬
    def age_sort_key(age_str: str) -> int:
        match = re.search(r'\d+', str(age_str))
        return int(match.group(0)) if match else 0
        
    age_order = sorted(df_filtered['연령대'].unique().tolist(), key=age_sort_key) 
    
    df_filtered['연도_str'] = df_filtered['연도'].astype(str)
    
    fig = px.bar(
        df_filtered,
        x='연령대',
        y='인구수',
        color='연도_str', 
        barmode='group', 
        title=f"연령대별 인구 구조 비교: {start_year}년 vs {end_year}년",
        labels={'연령대':'연령대', '인구수': '총 인구수', '연도_str': '연도'},
        category_orders={"연령대": age_order}, 
        color_discrete_map={str(start_year): '#3498DB', str(end_year): '#E74C3C'} 
    )

    fig.update_yaxes(tickformat=',.0f')
    st.plotly_chart(set_plotly_default(fig), use_container_width=True)


def plot_regional_choropleth(df_regional_long: pd.DataFrame, region_col_name: str, local_year: int, geo_json: Optional[Dict[str, Any]], key: str, color_label: str, is_data_available: bool, is_geo_available: bool):
    """
    지역별 인구/밀도 코로플레스 지도. 
    데이터 값이 0인 지역은 최저치 색상이 아닌 고정된 빨간색으로 표시됩니다.
    """
    if not is_data_available or not is_geo_available:
        return

    # 데이터 필터링 
    plot_data_full = df_regional_long.query('연도 == @local_year')
    
    if plot_data_full.empty or region_col_name not in plot_data_full.columns:
        st.error(f"선택된 연도 ({local_year}년)에 대한 데이터가 없거나, 색상 지정 컬럼 ({region_col_name})이 데이터프레임에 존재하지 않습니다.")
        return
        
    if not pd.api.types.is_numeric_dtype(plot_data_full[region_col_name]):
        st.error(f"색상을 지정할 컬럼 '{region_col_name}'의 데이터 타입이 숫자가 아닙니다. 현재 타입: {plot_data_full[region_col_name].dtype}")
        return
        
    # GeoJSON과의 매핑을 위해 불필요한 행 제거
    exclude_regions = ['합계', '전국', '수도권', '비수도권']
    plot_data = plot_data_full[~plot_data_full['지역'].isin(exclude_regions)].copy()
    
    if plot_data.empty:
        return

    feature_key = "properties.CTP_KOR_NM" 
    
    # 0 값과 양수 값 분리
    zero_data = plot_data[plot_data[region_col_name] == 0]
    positive_data = plot_data[plot_data[region_col_name] > 0]

    fig = go.Figure()

    # 양수 값에 대한 트레이스
    if not positive_data.empty:
        min_val = positive_data[region_col_name].min()
        max_val = positive_data[region_col_name].max()
        
        if min_val == max_val:
            max_val = min_val * 1.01 if min_val > 0 else 1 

        fig.add_trace(
            go.Choroplethmapbox(
                geojson=geo_json, 
                locations=positive_data['지역'], 
                z=positive_data[region_col_name], 
                featureidkey=feature_key,
                colorscale="Viridis", 
                zmin=min_val, 
                zmax=max_val,
                marker_opacity=0.8, 
                marker_line_width=0,
                hovertemplate='<b>%{location}</b><br>' + color_label + ': %{z:,.0f}<extra></extra>',
                name=f'{color_label} (양수)',
                colorbar=dict(title=color_label, len=0.8) 
            )
        )

    # 0 값에 대한 트레이스
    if not zero_data.empty:
        fixed_red_color = '#E74C3C' 
        fixed_red_scale = [[0, fixed_red_color], [1, fixed_red_color]] 

        fig.add_trace(
            go.Choroplethmapbox(
                geojson=geo_json, 
                locations=zero_data['지역'], 
                z=zero_data[region_col_name], 
                featureidkey=feature_key,
                colorscale=fixed_red_scale, 
                zmin=0,
                zmax=1, 
                showscale=False, 
                marker_opacity=0.8, 
                marker_line_width=0,
                hovertemplate='<b>%{location}</b><br>' + color_label + ': %{z:,.0f} (0값)<extra></extra>',
                name='0 값 지역 (빨간색)' 
            )
        )

    # 레이아웃 업데이트
    fig.update_layout(
        title_text=f"<b>{local_year}년</b> 지역별 {color_label} 분포", 
        title_x=0.5,
        mapbox_style="carto-positron", 
        mapbox_zoom=5.5, 
        mapbox_center={"lat": 36.3, "lon": 127.8}, # 대한민국 중앙 위치
        height=600, 
        margin={"r":0,"t":50,"l":0,"b":0},
        font=dict(family="Noto Sans KR, sans-serif", size=11), 
    )

    st.plotly_chart(fig, use_container_width=True)
