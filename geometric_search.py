import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely.affinity import translate
import numpy as np

def find_id_within_linearbuffer(gdf:gpd.GeoDataFrame, tp:tuple, angle:float, distance:float, buf:float) -> list:
    """
    주어진 점 P, 방위각 A, 거리 d, 버퍼 buf를 사용하여
    버퍼 내에 있는 점들을 선택하는 함수.

    Parameters:
    gdf (GeoDataFrame): 점들이 포함된 GeoDataFrame
    tp (Point): 기준 점
    angle (float): 방위각 (도 단위)
    distance (float): 거리
    buf (float): 버퍼 크기

    Returns:
    GeoDataFrame: 버퍼 내에 있는 점들
    """
    tp=Point(tp)
    # 방위각을 라디안으로 변환
    A_rad = angle * (np.pi / 180.0)
    # 새로운 점 계산
    end_point = translate(tp, xoff=d * np.cos(A_rad), yoff= distance * np.sin(A_rad))
    # 선 생성
    line = LineString([tp, end_point])
    # 버퍼 생성
    buffer = line.buffer(buf)

    # 버퍼 내에 있는 점 선택
    selected_points = gdf[gdf.geometry.within(buffer)]
    if not selected_points.empty:
        return selected_points['ID'].tolist()
    else:
        return None

def find_pnu_containing_point(gdf: gpd.GeoDataFrame, tp: tuple) -> list:  
    """
    점을 포함하는 피처들의 PNU 속성을 반환

    Parameters:
    gdf (GeoDataFrame): 점들이 포함된 GeoDataFrame
    tp (Point): 기준 점
    
    Returns: list    
    """  
    tp = Point(tp)
    # Point A를 포함하는 폴리곤 찾기
    containing_polygons = gdf[gdf.geometry.apply(lambda geom: tp.within(geom))]
    
    # "PNU" 속성 반환
    if not containing_polygons.empty:
        return containing_polygons['PNU'].tolist()
    else:
        return None


if __name__ == "__main__":
    # 예시 사용
    # 입력 데이터 로드
    data = pd.read_csv('input.csv')
    gdf = gpd.GeoDataFrame(data, geometry=gpd.points_from_xy(data.x, data.y))
    x, y = 0, 0  # 기준 점의 좌표
    A = 45  # 방위각
    d = 100  # 거리
    buf = 10  # 버퍼 크기

    selected_points = find_id_within_linearbuffer(gdf, (x, y), A, d, buf)

    # 결과 출력
    print(selected_points)



