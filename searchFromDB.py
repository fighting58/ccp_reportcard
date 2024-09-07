import geopandas as gpd
from shapely import Point


class NotDecodingError(Exception): ...

def cif2gpd(cif:str):
    if is_binary(cif):
        raise NotDecodingError(f"미복호화 에러: 복호화되지 않은 Cif입니다.")
    ...

def find_features_containing_point(point:Point, db:gpd.GeoDataFrame, fields:list=[]):
    ...

def is_binary(file_path):
    with open(file_path, 'rb') as file:
        while chunk := file.read(1024):
            if b'\0' in chunk:
                return True
            return False
