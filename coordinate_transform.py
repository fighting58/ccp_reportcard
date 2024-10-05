from pyproj import Transformer

ESPG_NUM = {"WGS84": 4326,  # 경위도 좌표
            "GRS80": 5186}  # 세계측지계(중부) 좌표


class CoordinateTransformer:
    def __init__(self, input_system=ESPG_NUM["WGS84"], output_system=ESPG_NUM["GRS80"]):
        self._input_system = input_system
        self._output_system = output_system

    @property
    def input_system(self):
        return self._input_system

    @property
    def output_system(self):
        return self._output_system

    @input_system.setter
    def input_system(self, value):
        self._input_system = value

    @output_system.setter
    def output_system(self, value):
        self._output_system = value

    def __set_transformer(self, reverse=False):
        self.transformer = Transformer.from_crs(f"EPSG:{self.input_system}", f"EPSG:{self.output_system}", always_xy=True)
        if reverse:
            self.transformer = Transformer.from_crs(f"EPSG:{self.output_system}", f"EPSG:{self.input_system}", always_xy=True)

    def __call__(self, **kargs):
        """
        WGS84(ESPG:4326, 경위도좌표) <-> GRS80(EPSG:5186, 세계측지계(중부)) 좌표변환
        
        Kargs:
        - lon: longitude (float): 경도
        - lat: latitude (float): 위도
        - x : x좌표 (float): GRS80 세계측지계(중부) x좌표
        - y : y좌표 (float): GRS80 세계측지계(중부) y좌표

        Returns:
        - tuple: 변환된 좌표 (x, y) : kargs로 lon, lat이 주어질 경우
        - tuple: 변환된 좌표 (lon, lat) : kargs로 x, y가 주어질 경우
        """

        lon = kargs.get("lon")
        lat = kargs.get("lat")
        ix = kargs.get("x")
        iy = kargs.get("y")
        
        if lon and lat:
            self.__set_transformer()
            y, x = self.transformer.transform(lon, lat)
            
        elif ix and iy:
            self.__set_transformer(reverse=True)
            x, y = self.transformer.transform(iy, ix)

        return x, y

# 사용 예제
if __name__ == "__main__":
    transformer = CoordinateTransformer()

    longitude = 127.2013584  # 예시 경도
    latitude = 37.2323391   # 예시 위도
    ix = 515107.32 
    iy = 221066.07
    x, y = transformer(lon=longitude, lat=latitude)
    print(f"변환된 좌표: x={x}, y={y}")
    x, y = transformer(x=ix, y=iy)
    print(f"변환된 좌표: lon={x}, lat={y}")

