from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

def get_exif_data(image_path:str) -> list:
    image = Image.open(image_path)
    exif_data = image._getexif()
    if not exif_data:
        return None

    exif = {}
    for tag, value in exif_data.items():
        decoded = TAGS.get(tag, tag)
        if decoded == "GPSInfo":
            gps_data = {}
            for t in value:
                sub_decoded = GPSTAGS.get(t, t)
                gps_data[sub_decoded] = value[t]
            exif[decoded] = gps_data
        else:
            exif[decoded] = value
    print(exif)
    return exif

def get_gps_info(image_path: str) -> tuple:
    """
    사진 이미지로부터 GPS 정보를 반환
    pram image_path: (str) 사진 파일 경로
     
    return: (tuple) (lon, lat, direction)반환
    """
    exif_info = get_exif_data(image_path)
    lon, lat = get_gps_position(exif_info)
    direction = get_gps_direction(exif_info)
    return lon, lat, direction

def get_gps_position(exif_data:list) -> tuple:
    """
    exif_data로부터 (lon, lat)튜플형태의 좌표를 반환
    (튜플의 각 원소의 단위는 degree)
    """
    gps_info = exif_data.get("GPSInfo", {})
    lon = gps_info.get("GPSLongitude", ())
    lat = gps_info.get("GPSLatitude", ())

    if lon and lat:               # lon, lat tag가 있으면 
        return dms2degree(lon), dms2degree(lat)        
    return None

def get_gps_direction(exif_data:list) -> tuple:
    """
    exif_data로부터 방위각을 반환(단위 degree)
    """
    gps_info = exif_data.get("GPSInfo", {})
    direction = gps_info.get("GPSImgDirection", ())
    if direction:                 # GPSImgDirection tag가 있으면 
        return direction      
    return None

def dms2degree(dms: tuple) -> float:
    """
    exif_data의 lon 혹은 lat을 degree로 변환
    """
    if dms:
        d, m, s = dms
        return float(d + (m/60) + (s/3600))
    return None


if __name__ == "__main__":
    image1 = 'Exif_info/202409041547290009.jpg'
    from coordinate_transform import CoordinateTransformer
    import webbrowser

    exif_data1 = get_gps_info(image1)
    transformer = CoordinateTransformer()

    if exif_data1:
        lon, lat, direction = exif_data1
        print(exif_data1)
        x, y = transformer(lon=lon, lat=lat)
        if (lon, lat) is not None:
            print(f"경위도: ({lon}, {lat}) degrees")
            print(f'세계중부좌표: ({x}, {y})')
        else:
            print("경위도 정보를 찾을 수 없습니다.")
    else:
        print("EXIF 데이터를 찾을 수 없습니다.")

    url_kakao_form = "https://map.kakao.com/link/map/{0}, {2}, {1}"
    webbrowser.open(url_kakao_form.format("test", lon, lat))
    


 