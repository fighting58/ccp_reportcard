import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString
from shapely.affinity import translate
import numpy as np

def find_id_within_linearbuffer(gdf:gpd.GeoDataFrame, tp:tuple, angle:float, distance:float, buf:float) -> gpd.GeoDataFrame:
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
        return selected_points
    else:
        return None
    
def convert_to_geodataframe(df: pd.DataFrame, x_col: str='XX', y_col: str='YY') -> gpd.GeoDataFrame:
        """
        DataFrame 포인트 타입 GeoDataFrame으로 변환
        
        Parameters:
        df (DataFrame): 변환에 필요한 DataFrame
        x_col (str): x좌표가 들어있는 df의 컬럼명
        y_col (str): y좌표가 들어있는 df의 컬럼명

        """
        # 'XX'와 'YY' 열을 사용하여 Point 객체 생성
        geometry = [Point(xy) for xy in zip(df[x_col], df[y_col])]
        
        # GeoDataFrame 생성
        gdf = gpd.GeoDataFrame(df, geometry=geometry)
        
        return gdf
    
def find_features_within_buffer(gdf:gpd.GeoDataFrame, tp:tuple, buf:float) -> gpd.GeoDataFrame:
    """
    주어진 점 P, 방위각 A, 거리 d, 버퍼 buf를 사용하여
    버퍼 내에 있는 점들을 선택하는 함수.

    Parameters:
    gdf (GeoDataFrame): 점들이 포함된 GeoDataFrame
    tp (Point): 기준 점
    buf (float): 버퍼 크기

    Returns:
    GeoDataFrame: 버퍼 내에 있는 점들
    """
    tp = Point(tp) 
    buffer = tp.buffer(buf, 16)  # tp주변, 16각형(default:8)

    # 버퍼 내에 있는 점 선택
    selected_points = gdf[gdf.geometry.within(buffer)]
    if not selected_points.empty:
        return selected_points
    else:
        return None

def find_attributes_containing_point(gdf: gpd.GeoDataFrame, tp: tuple, colnames:list) -> list:  
    """
    점을 포함하는 피처들의 PNU 속성을 반환

    Parameters:
    gdf (GeoDataFrame): 점들이 포함된 GeoDataFrame
    tp (Point): 기준 점
    
    Returns: list    
    """  
    tp = Point(tp)
    # Point A를 포함하는 폴리곤 찾기
    containing_polygons = gdf[gdf.contains(tp)]
    
    # "PNU" 속성 반환
    if not containing_polygons.empty:
        return containing_polygons[colnames]
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



