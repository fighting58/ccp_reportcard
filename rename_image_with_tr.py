import sys
import os
import pandas as pd
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QFileDialog, QLabel
from PySide6.QtCore import Qt
from PIL import Image
import PIL.ExifTags as ExifTags
import numpy as np
from coordinate_transform import CoordinateTransformer
from geometric_search import find_id_within_linearbuffer, find_features_within_buffer, convert_to_geodataframe


class MyDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.tr_df = None  # tr.dat DataFrame
        self.pic_path = None  # 이미지 폴더 경로

        self.setWindowTitle("EXIF 정보 처리 다이얼로그")
        self.setGeometry(100, 100, 400, 200)

        # 레이아웃 설정
        layout = QVBoxLayout()

        # tr.dat 버튼 생성
        self.tr_button = QPushButton("tr.dat 파일 불러오기")
        self.tr_button.clicked.connect(self.load_tr_dat)
        layout.addWidget(self.tr_button)

        # Pictures 버튼 생성
        self.pictures_button = QPushButton("이미지 폴더 선택")
        self.pictures_button.clicked.connect(self.load_pictures_folder)
        layout.addWidget(self.pictures_button)

        # 실행 버튼 생성
        self.run_button = QPushButton("실행")
        self.run_button.clicked.connect(self.run_process)
        layout.addWidget(self.run_button)

        # 상태 표시 레이블
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        self.setLayout(layout)


    def load_tr_dat(self):
        # QFileDialog를 통해 tr.dat 파일 선택
        file_path, _ = QFileDialog.getOpenFileName(self, "Open tr.dat", "", "Data Files (*.dat)")
        NUM, X, Y = [], [], [] 
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.replace('\t', ' ')
                        while True:
                            if "  " in line:
                                line = line.replace("  ", " ")
                            else:
                                break
                        n, x, y = line.strip().split(' ')
                        NUM.append(n)
                        X.append(int(x)/100)
                        Y.append(int(y)/100)
                self.tr_df = pd.DataFrame(data=list(zip(NUM, X, Y)), columns=["Point", "X", "Y"])
                self.status_label.setText(f"Loaded tr.dat: {file_path}")
                print(self.tr_df)
            except Exception as e:
                self.status_label.setText(f"Failed to load tr.dat: {e}")

    def load_pictures_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "이미지 폴더 선택")
        if folder:
            self.pic_path = folder
            print("이미지 폴더 선택 완료:", self.pic_path)

    def run_process(self):
        if self.tr_df is None or self.pic_path is None:
            self.status_label.setText("tr.dat 파일 또는 이미지 폴더가 설정되지 않았습니다.")
            return

        # 이미지 파일 처리
        pic_file = []
        lon_list = []
        lat_list = []

        for root, dirs, files in os.walk(self.pic_path):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(root, file)
                    pic_file.append(file)
                    
                    # EXIF 정보 추출
                    img = Image.open(file_path)
                    exif_data = img._getexif()
                    if exif_data:
                        gps_info = {
                            ExifTags.TAGS.get(tag): exif_data[tag]
                            for tag in exif_data
                            if tag in ExifTags.TAGS and ExifTags.TAGS[tag] == "GPSInfo"
                        }
                        if gps_info:
                            lat, lon = self.extract_lat_lon(gps_info.get('GPSInfo', {}))
                            lon_list.append(lon)
                            lat_list.append(lat)
                        else:
                            lon_list.append(None)
                            lat_list.append(None)
                    else:
                        lon_list.append(None)
                        lat_list.append(None)
                    img = None

        # DataFrame 생성
        pic_df = pd.DataFrame(data=list(zip(pic_file, lon_list, lat_list)), columns=['file', 'Lon', 'Lat'])
        pic_df.dropna(inplace=True)  # GPS 정보가 없으면 제거
        if pic_df.empty:
            self.status_label.setText("Exif 정보가 없습니다.")
            return
        else:
            self.status_label.setText("이미지 DataFrame 생성 완료")

        # 좌표 변환 및 거리 계산 처리
        # self.transform 함수를 벡터화
        vectorized_transform = np.vectorize(self.transform)
        pic_df['XX'], pic_df['YY'] = vectorized_transform(pic_df['Lon'], pic_df['Lat'])


        self.calculate_and_rename_files(pic_df)

    def extract_lat_lon(self, gps_info):
        # GPS 정보에서 위도, 경도 추출
        def convert_to_degrees(value):
            d = float(value[0])
            m = float(value[1]) / 60.0
            s = float(value[2]) / 3600.0
            return d + m + s

        lat = convert_to_degrees(gps_info.get(2, (0, 0, 0)))
        lon = convert_to_degrees(gps_info.get(4, (0, 0, 0)))
        
        return lat, lon

    def transform(self, lon, lat):
        # 경도, 위도를 직교 좌표로 변환
        transformer = CoordinateTransformer()
        xx, yy = transformer(lon=lon, lat=lat)
        return xx, yy

    def calculate_and_rename_files(self, pic_df):
        # tr_df의 (X, Y)와 pic_df의 (XX, YY) 사이의 거리를 계산 후 이름 변경
        for idx, tr_row in self.tr_df.iterrows():
            tr_point = tr_row['X'], tr_row['Y']

            # DataFrame을 GeoDataFrame으로 변환
            pic_gdf = convert_to_geodataframe(pic_df)

            # 버퍼 범위내의 이미지 추출
            selected_gdf = find_features_within_buffer(pic_gdf, tr_point, 30)
            
            if not selected_gdf is None:
                new_gdf= selected_gdf.copy()
                # 거리 계산 (유클리드 거리)
                new_gdf['distance'] = np.sqrt((new_gdf['XX'] - tr_point[0]) ** 2 + (new_gdf['YY'] - tr_point[1]) ** 2)

                # 가장 가까운 파일 찾기
                closest_pic = new_gdf.loc[new_gdf['distance'].idxmin()]

                # 파일 이름을 점번호로 변경
                old_name = os.path.join(self.pic_path, closest_pic['file'])
                new_name = os.path.join(self.pic_path, str(tr_row['Point']) + os.path.splitext(closest_pic['file'])[1])
                os.rename(old_name, new_name)
                print(f"파일 이름 변경: {old_name} -> {new_name}")

                # DataFrame에서 해당 파일 삭제
                pic_df = pic_df[pic_df.index != closest_pic.name]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MyDialog()
    dialog.show()
    sys.exit(app.exec())

    """
    
    
    Pyside6 라이브러리를 이용해서 다이얼로그를 만들려고 해.
  1. tr.dat 버튼
    - tr.dat 파일 불러오기, QFileDialog    
    - tr.dat를 pandas dataframe으로 변환
    - tr.dat파일: 점번호, X좌표, Y좌표로 구성된 값을 가지며 tab으로 구분
    - tr_df 변수에 저장
  2. Pictures 버튼
    - 이미지 폴더 불러오기
    - pic_path 변수에 저장
  3. 실행 버튼
    - pic_path 내에 존재하는 이미지 파일들에 대해 다음 리스트를 생성 후 DataFrame으로 변환
      - pic_file: filename list
      - lon_list: 이미지 파일의 exif 정보 중 longitude
      - lat_list: 이미지 파일의 exif 정보 중 latitude
    - pic_df = pd.DataFrame(data=list(zip(pic_file, lon_list, lat_list)), columns=['file', 'Lon', 'Lat'])
    - pic_df의 Lon, Lat 을 transform() 변환함수를 통해 직교좌표 XX, YY로 변환 
    - tr_df의 (X, Y)와 pic_df의 (XX, YY) 사이의 거리를 구해 가장 가까운 pic_df의 file을 이름을 tr_df의 점번호로 변경(os.rename(file, 점번호))하고 pic_df에서 drop
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    """