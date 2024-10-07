from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import piexif
import webbrowser
import os

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
    lon, lat = _get_gps_position(exif_info)
    direction = _get_gps_direction(exif_info)
    return lon, lat, direction

def _get_gps_position(exif_data:list) -> tuple:
    """
    exif_data로부터 (lon, lat)튜플형태의 좌표를 반환
    (튜플의 각 원소의 단위는 degree)
    """
    gps_info = exif_data.get("GPSInfo", {})
    lon = gps_info.get("GPSLongitude", ())
    lat = gps_info.get("GPSLatitude", ())

    if lon and lat:               # lon, lat tag가 있으면 
        return dms2degree(lon), dms2degree(lat)        
    return None, None

def _get_gps_direction(exif_data:list) -> tuple:
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

def degree2dms(degree):
    """
    도(degree) 값을 도, 분, 초(DMS)로 변환하는 함수.

    Args:
    - degree (float): 변환할 도 값.

    Returns:
    - tuple: (도, 분, 초) 형식의 튜플
    """
    d = int(degree)  # 도
    m_float = (degree - d) * 60
    m = int(m_float)  # 분
    s = (m_float - m) * 60  # 초
    
    return d, m, s


def degree_to_dms_piexif(degree):
    """
    도(degree) 값을 piexif에서 사용하는 도, 분, 초(DMS) 형식으로 변환.

    Args:
    - degree (float): 변환할 도 값.

    Returns:
    - tuple: ((도, 분모), (분, 분모), (초*100, 100)) 형식의 튜플
    """
    d, m, s = degree2dms(degree)
    
    # GPS 정보는 (정수, 분모) 형식으로 표현되므로 (초는 100을 곱해 분수로 만듦)
    return ((d, 1), (m, 1), (int(s * 10000000000), 10000000000))  # 삼성(10000000)

# EXIF를 수정하는 함수
def update_image_gps_exif(image_path, lon=None, lat=None):
    """
    이미지 파일의 EXIF에 GPS 정보를 추가 또는 수정하는 함수.

    Args:
    - image_path (str): 이미지 파일의 경로.
    - lon (float): 경도(degree).
    - lat (float): 위도(degree).
    """
    # 이미지 열기
    image = Image.open(image_path)
    path, filename = os.path.split(image_path)

    # EXIF 데이터 읽기 (EXIF 데이터가 없을 수도 있으므로 try-except 사용)
    try:
        exif_dict = piexif.load(image.info['exif'])
    except KeyError:
        # EXIF 데이터가 없을 경우 빈 딕셔너리 생성
        exif_dict = {"GPS": {}}
    
    # 위도와 경도를 DMS 형식으로 변환하여 업데이트
    if not lat is None:
        dms_latitude = degree_to_dms_piexif(lat)
        lat_ref = "N" if lat >= 0 else "S"  # 위도 및 경도 방향 설정 (북위/남위, 동경/서경)
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitude] = dms_latitude
        exif_dict["GPS"][piexif.GPSIFD.GPSLatitudeRef] = lat_ref
    if not lon is None:
        dms_longitude = degree_to_dms_piexif(lon)
        lon_ref = "E" if lon >= 0 else "W"  # 위도 및 경도 방향 설정 (북위/남위, 동경/서경)
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitude] = dms_longitude
        exif_dict["GPS"][piexif.GPSIFD.GPSLongitudeRef] = lon_ref

    # 수정된 EXIF 데이터를 바이너리로 변환
    exif_bytes = piexif.dump(exif_dict)

    # EXIF 데이터를 포함하여 이미지 저장
    updated_image_path = os.path.join(path, "updated_" + filename)
    image.save(updated_image_path, exif=exif_bytes)

    print(f"GPS 정보가 수정된 이미지가 {updated_image_path}로 저장되었습니다.")

def show_on_kakao(tag:str, lon:float, lat:float) -> None:
    """
    kakao map에서 위치 확인
    
    param:
        tag (str): 위치에 대한 설명
        lon (float): 경도
        lat (float): 위도
    """
    url_kakao_form = "https://map.kakao.com/link/map/{0}, {2}, {1}"
    webbrowser.open(url_kakao_form.format(tag, lon, lat))


if __name__ == "__main__":
    image1 = 'Exif_info/202409041527070009.jpg'
    image2 = 'Exif_info/202409041527190009.jpg'
    image3 = 'Exif_info/202409041547290009.jpg'
    from coordinate_transform import CoordinateTransformer
    import webbrowser

    exif_data1 = get_gps_info(image1)
    transformer = CoordinateTransformer()

    if exif_data1:
        lon, lat, direction = exif_data1
        x, y = transformer(lon=lon, lat=lat)
        if (lon, lat) is not None:
            print(f"경위도: ({lon}, {lat}) degrees")
            print(f'세계중부좌표: ({x}, {y})')
        else:
            print("경위도 정보를 찾을 수 없습니다.")
    else:
        print("EXIF 데이터를 찾을 수 없습니다.")

    ### kakao map에서 확인
    # url_kakao_form = "https://map.kakao.com/link/map/{0}, {2}, {1}"
    # webbrowser.open(url_kakao_form.format("test", lon, lat))

    update_image_gps_exif(image1, 127.23821002720551, 37.23441623266602)
    update_image_gps_exif(image2, 127.23755300291091, 37.233759159087214)
    update_image_gps_exif(image3, 127.23739844115542, 37.23488910864183)
    
