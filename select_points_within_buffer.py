import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely.affinity import translate
import numpy as np

# 입력 데이터 로드
data = pd.read_csv('input.csv')
gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.x, data.y))

def select_points_within_buffer(gdf, P, A, d, buf):
    """
    주어진 점 P, 방위각 A, 거리 d, 버퍼 buf를 사용하여
    버퍼 내에 있는 점들을 선택하는 함수.

    Parameters:
    gdf (GeoDataFrame): 점들이 포함된 GeoDataFrame
    P (Point): 기준 점
    A (float): 방위각 (도 단위)
    d (float): 거리
    buf (float): 버퍼 크기

    Returns:
    GeoDataFrame: 버퍼 내에 있는 점들
    """
    # 방위각을 라디안으로 변환
    A_rad = A * (np.pi / 180.0)

    # 새로운 점 계산
    end_point = translate(P, xoff=d * np.cos(A_rad), yoff=d * np.sin(A_rad))

    # 선 생성
    line = LineString([P, end_point])

    # 버퍼 생성
    buffer = line.buffer(buf)

    # 버퍼 내에 있는 점 선택
    selected_points = gdf[gdf.geometry.within(buffer)]
    
    return selected_points

# 예시 사용
x, y = 0, 0  # 기준 점의 좌표
A = 45  # 방위각
d = 100  # 거리
buf = 10  # 버퍼 크기

selected_points = select_points_within_buffer(gdf, Point(x, y), A, d, buf)

# 결과 출력
print(selected_points)
