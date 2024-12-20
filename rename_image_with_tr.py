import sys
import os
import pandas as pd
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton, QFileDialog, QLabel, QGridLayout, QFrame
from PySide6.QtCore import Qt
import numpy as np
from coordinate_transform import CoordinateTransformer
from geometric_search import find_features_within_buffer, convert_to_geodataframe
from Exif_info import get_gps_info

class DialogRenameImage(QDialog):
    def __init__(self):
        super().__init__()

        self.tr_df = None  # tr.dat DataFrame
        self.pic_path = None  # 이미지 폴더 경로
        self._tr = None     # tr.dat 파일 경로

        self.setWindowTitle("TR 점번호로 파일명 변경")
        self.setGeometry(100, 100, 500, 200)

        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 10, 0, 0)
        gridlayout = QGridLayout()
        gridlayout.setContentsMargins(10, 10, 10, 10)


        # tr.dat 버튼 생성
        self.tr_button = QPushButton("tr.dat 파일 입력")
        self.tr_button.setFixedWidth(120)
        self.tr_button.clicked.connect(self.load_tr_dat)
        gridlayout.addWidget(self.tr_button, 0, 0, 1, 1)

        self.tr_label = QLabel("tr.dat가 아직 입력되지 않았습니다.")
        gridlayout.addWidget(self.tr_label, 1, 0, 1, 3)

        # Pictures 버튼 생성
        self.pictures_button = QPushButton("이미지 폴더 선택")
        self.pictures_button.setFixedWidth(120)
        self.pictures_button.clicked.connect(self.load_pictures_folder)
        gridlayout.addWidget(self.pictures_button, 2, 0, 1, 1)

        self.pictures_label = QLabel("사진 폴더가 아직 선택되지 않았습니다.")
        gridlayout.addWidget(self.pictures_label, 3, 0, 1, 3)

        # 실행 버튼 생성
        self.run_button = QPushButton("실행")
        self.run_button.setFixedWidth(120)
        self.run_button.clicked.connect(self.run_process)
        gridlayout.addWidget(self.run_button, 4, 2, 1, 1)

        # 상태 표시 레이블
        frame = QFrame(self)
        frame.setObjectName('statusbar')
        vlayout = QVBoxLayout(frame)
        vlayout.setContentsMargins(10, 0, 0, 0)
        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignRight)
        frame.setFixedHeight(24)
        vlayout.addWidget(self.status_label)
        layout.addLayout(gridlayout)
        layout.addWidget(frame)
        self.setLayout(layout)

    @property
    def tr(self):
        return self._tr

    @tr.setter
    def tr(self, tr):
        self._tr = tr
        self.tr_label.setText(f"{tr}")

    def get_tr_dat(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open tr.dat", "", "Data Files (*.dat)")
        if file_path:
            self.tr = file_path
            self.status_label.setText(f"tr.dat 선택: {self.tr}")
            return file_path
        return None

    def load_tr_dat(self):
        tr_dat = self.tr
        if tr_dat is None:
            tr_dat = self.get_tr_dat()
        
        NUM, X, Y = [], [], []
        
        if tr_dat:
            try:
                with open(tr_dat, 'r') as f:
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
                
            except Exception as e:
                self.status_label.setText(f"Failed to load tr.dat: {e}")
        else:
            self.status_label.setText(f"tr.dat 파일을 선택해주세요.")

    def load_pictures_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "이미지 폴더 선택")
        if folder:
            self.pic_path = folder
            self.pictures_label.setText(f"{folder}")
            self.status_label.setText(f"이미지 폴더 선택: {self.pic_path}")

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
                    lon, lat, _ = get_gps_info(file_path)
                    lon_list.append(lon)
                    lat_list.append(lat)

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
            selected_gdf = find_features_within_buffer(pic_gdf, tr_point, 50)  #<========= 중요. 촬영점에서의 버퍼 구간설정=========
            
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
    from pathlib import Path
    app = QApplication(sys.argv)
    dialog = DialogRenameImage()
    dialog.setStyleSheet(Path('dialogrenameimage.qss').read_text())
    dialog.show()
    sys.exit(app.exec())

