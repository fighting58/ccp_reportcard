# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication, QFileDialog, QWidget
from PyQt5 import uic
import sys
import shapefile
import time
import pandas as pd
import os
import pyproj

form_class = uic.loadUiType('UI/cif2shp_ui.ui')[0]

class MyCIF(QWidget, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.option = 0  # 0:개별지적, 1: 연속지적, 2: 모두
        self.btnGetCifs.clicked.connect(self.getcifs)
        self.btnRun.clicked.connect(self.run)
        self.btnRemove.clicked.connect(self.removeitems)
        self.optOption1.clicked.connect(self.setoption)
        self.optOption2.clicked.connect(self.setoption)
        self.optOption3.clicked.connect(self.setoption)

    def setoption(self):
        if self.optOption1.isChecked():
            self.option = 0
        if self.optOption2.isChecked():
            self.option = 1
        if self.optOption3.isChecked():
            self.option = 2

    def returnSpaceifNull(self, s):
        return s if len(s) > 0 else ' '

    def getcifs(self):
        cifs, _ = QFileDialog.getOpenFileNames(self, caption="Select Cif file", directory='', filter='cif file(*.cif)')
        self.lstCifList.addItems(cifs)

    def code2jimok(self, code):
        jimok = [u'전', u'답', u'과', u'목', u'임', u'광', u'염', u'대', u'장', u'학', u'차', u'주', u'창', u'도', u'철',
                 u'제', u'천', u'구', u'유', u'양', u'수', u'공', u'체', u'원', u'종', u'사', u'묘', u'잡']
        try:
            inx = int(code)
            if 0 < inx < 29:
                return jimok[inx - 1]
            else:
                raise Exception("Out of Range: JimoK index")
        except:
            return ' '

    def pnu2jibun(self, pnu):
        bon = int(pnu[-8:-4])
        bu = int(pnu[-4:])
        mt = '산' if pnu[-9:-8] == '2' else ''
        jibun = '-'.join([str(bon), str(bu)])
        return ''.join([mt, jibun]).replace('-0', '')

    def code2wonjum(self, code):
        wonjum = [u"동부원/지점", u"중부원/지점", u"서부원/지점", u"망산원/지점", u"계양원점", u"조본원점", u"가리원점", u"동경원점",
                  u"고초원점", u"율곡원점", u"현창원점", u"구암원점", u"금산원점", u"소라원점", u"특별소삼각측량지역", u"특별도근측량지역",
                  u"특별세부축도지역"]
        try:
            inx = int(code)
            if 0 < inx < 18:
                return wonjum[inx - 1]
            elif inx == 32:
                return u'세계중부원점'
            else:
                raise Exception("Out of Range: Wonjum index")
        except:
            return ' '

    def makeShpOBND(self, cif):
        print(u"Transform Start: 개별지적")
        stime = time.time()
        shp = cif.replace(".cif", u"_개별지적.shp").replace(".Cif", u"_개별지적.shp")

        with shapefile.Writer(shp, encoding='euc-kr') as w:
            w.field('PNU', 'C', size='19')
            w.field('DOM', 'C')
            w.field('SCALE', 'C')
            w.field('JIBUN', 'C')
            w.field('REGAREA', 'C')
            w.field('CALAREA', 'C')
            w.field('MOVECODE', 'C')
            w.field('MOVEDATE', 'C')
            w.field('REFJIBUN', 'C')
            w.field('SAUPCODE', 'C')
            w.field('SAUPBUNHO', 'C')
            w.field('OWNCHGCD', 'C')
            w.field('OWNDATE', 'C')
            w.field('REGNUM', 'C')
            w.field('OWNER', 'C')
            w.field('ADDRESS', 'C', size='255')
            w.field('OWNGUBUNCD', 'C')
            w.field('GONGYU', 'C')
            w.field('REGMAP', 'C')
            w.field('YONGDO', 'C')
            w.field('LAW', 'C', size='255')
            w.field('OTHERLAW', 'C', size='255')
            w.field('REGULAR', 'C')
            w.field('LAWORDER', 'C')
            w.field('PRICE', 'C')
            w.field('WONJUM', 'C')
            w.field('LASTNUM', 'C')

            rec = []
            PNU = DOM = SCALE = JIBUN = REGAREA = CALAREA = MOVECODE = MOVEDATE = REFJIBUN = SAUPCODE = SAUPBUNHO = \
                OWNCHGCD = OWNDATE = REGNUM = OWNER = ADDRESS = OWNGUBUNCD = GONGYU = REGMAP = YONGDO = LAW = \
                OTHERLAW = REGULAR = LAWORDER = PRICE = WONJUM = LASTNUM = " "

            try:
                with open(cif, "r") as f:
                    while 1:
                        data = f.readline().strip()
                        if data == u'<필지S>':
                            data = f.readline().strip()
                            data = PNU = f.readline().strip()
                            rec.append(PNU)
                        if data == u':필계점':
                            parts = int(f.readline().strip())
                            pointcounts = []
                            for i in range(parts):
                                pointcounts.append(int(f.readline().strip()))
                                COORDS = [[] for i in range(parts)]
                            for part, counts in enumerate(pointcounts):
                                for i in range(counts):
                                    y, x = f.readline().strip().split()
                                    COORDS[part].append([float(x), float(y)])
                        if data == u':도면번호':
                            DOM = self.returnSpaceifNull(f.readline().strip())
                        if data == u':축척코드':
                            SCALE = self.returnSpaceifNull(f.readline().strip())
                        if data == u':지목코드':
                            JIMOK = self.returnSpaceifNull(f.readline().strip())
                            JIBUN = self.pnu2jibun(PNU) + self.code2jimok(JIMOK)
                        if data == u':대장면적':
                            REGAREA = self.returnSpaceifNull(f.readline().strip())
                        if data == u':좌표면적':
                            CALAREA = self.returnSpaceifNull(f.readline().strip())
                        if data == u':토지이동사유코드':
                            MOVECODE = self.returnSpaceifNull(f.readline().strip())
                        if data == u':토지이동일자':
                            MOVEDATE = self.returnSpaceifNull(f.readline().strip())
                        if data == u':토지이동사유관련지번':
                            REFJIBUN = self.returnSpaceifNull(f.readline().strip())
                        if data == u':사업시행신고구분코드':
                            SAUPCODE = self.returnSpaceifNull(f.readline().strip())
                        if data == u':사업시행지번호':
                            SAUPBUNHO = self.returnSpaceifNull(f.readline().strip())
                        if data == u':소유권변동원인구분코드':
                            OWNCHGCD = self.returnSpaceifNull(f.readline().strip())
                        if data == u':소유권변동일자':
                            OWNDATE = self.returnSpaceifNull(f.readline().strip())
                        if data == u':등록번호':
                            REGNUM = self.returnSpaceifNull(f.readline().strip())
                        if data == u':성명및명칭':
                            OWNER = self.returnSpaceifNull(f.readline().strip())
                        if data == u':주소':
                            ADDRESS = self.returnSpaceifNull(f.readline().strip())
                        if data == u':소유구분코드':
                            OWNGUBUNCD = self.returnSpaceifNull(f.readline().strip())
                        if data == u':공유구분코드':
                            GONGYU = self.returnSpaceifNull(f.readline().strip())
                        if data == u':도면구분':
                            REGMAP = self.returnSpaceifNull(f.readline().strip())
                        if data == u':용도지역':
                            YONGDO = self.returnSpaceifNull(f.readline().strip())
                        if data == u':국토계획법률':
                            LAW = self.returnSpaceifNull(f.readline().strip())
                        if data == u':다른법령':
                            OTHERLAW = self.returnSpaceifNull(f.readline().strip())
                        if data == u':토지이용규제':
                            REGULAR = self.returnSpaceifNull(f.readline().strip())
                        if data == u':시행령':
                            ORDER = self.returnSpaceifNull(f.readline().strip())
                        if data == u':공시지가가격(m2당)':
                            PRICE = self.returnSpaceifNull(f.readline().strip())
                        if data == u':원점코드':
                            WONJUM = self.code2wonjum(self.returnSpaceifNull(f.readline().strip()))
                        if data == u':종번':
                            LASTNUM = self.returnSpaceifNull(f.readline().strip())
                        if data == u'<필지E>':
                            w.poly(COORDS)
                            w.record(PNU, DOM, SCALE, JIBUN, REGAREA, CALAREA, MOVECODE, MOVEDATE, REFJIBUN, SAUPCODE,
                                     SAUPBUNHO, OWNCHGCD, OWNDATE, REGNUM, OWNER, ADDRESS, OWNGUBUNCD, GONGYU, REGMAP,
                                     YONGDO, LAW, OTHERLAW, REGULAR, LAWORDER, PRICE, WONJUM, LASTNUM)
                        if data == u'<연속필지S>' or data == 'EOF':
                            break
            except Exception as e:
                print(e)

        print(u"Transform End: 개별지적")

        # # 좌표계 설정: Korea_2000_Korea_Central_Belt_2010, ESPG:5186
        self.set_crs(shp, 5186)

        etime = time.time()
        print(f'Time elapse: {etime-stime}')

        return shp

    def set_crs(self, shp:str, espg:int):
        crs = pyproj.CRS.from_epsg(espg)
        prj_path = shp.replace('.shp', '.prj')
        with open(prj_path, 'w', encoding='euc-kr') as prj_file:
            prj_file.write(crs.to_wkt(pyproj.enums.WktVersion.WKT1_ESRI))

    def __makeDataFrameOBND(self, cif):
        """ cif를 DataFrame으로 변환"""
        stime = time.time()
        df = {'PNU': [], 'DOM': [], 'SCALE': [], 'JIBUN': [], 'REGAREA':[], 'CALAREA': [], 'MOVECODE': [],
              'MOVEDATE': [], 'REFJIBUN': [], 'SAUPCODE': [], 'SAUPBUNHO': [], 'OWNCHGCD': [], 'OWNDATE': [],
              'REGNUM': [], 'OWNER': [], 'ADDRESS': [], 'OWNGUBUNCD': [], 'GONGYU': [], 'REGMAP': [], 'YONGDO': [],
              'LAW': [], 'OTHERLAW': [], 'REGULAR': [], 'LAWORDER': [], 'PRICE': [], 'WONJUM': [], 'LASTNUM': []}

        try:
            with open(cif, "r") as f:
                while 1:
                    data = f.readline().strip()
                    if data == u'<필지S>':
                        data = f.readline().strip()
                        data = PNU = f.readline().strip()
                        df['PNU'].append(PNU)
                    if data == u':필계점':
                        parts = int(f.readline().strip())
                        pointcounts = []
                        for i in range(parts):
                            pointcounts.append(int(f.readline().strip()))
                            COORDS = [[] for i in range(parts)]
                        for part, counts in enumerate(pointcounts):
                            for i in range(counts):
                                y, x = f.readline().strip().split()
                                COORDS[part].append([float(x), float(y)])
                    if data == u':도면번호':
                        DOM = self.returnSpaceifNull(f.readline().strip())
                        df['DOM'].append(DOM)
                    if data == u':축척코드':
                        SCALE = self.returnSpaceifNull(f.readline().strip())
                        df['SCALE'].append(SCALE)
                    if data == u':지목코드':
                        JIMOK = self.returnSpaceifNull(f.readline().strip())
                        JIBUN = self.pnu2jibun(PNU) + self.code2jimok(JIMOK)
                        df['JIMOK'].append(JIMOK)
                        df['JIBUN'].append(JIBUN)
                    if data == u':대장면적':
                        REGAREA = self.returnSpaceifNull(f.readline().strip())
                        df['REGAREA'].append(REGAREA)
                    if data == u':좌표면적':
                        CALAREA = self.returnSpaceifNull(f.readline().strip())
                        df['CALAREA'].append(CALAREA)
                    if data == u':토지이동사유코드':
                        MOVECODE = self.returnSpaceifNull(f.readline().strip())
                        df['MOVECODE'].append(MOVECODE)
                    if data == u':토지이동일자':
                        MOVEDATE = self.returnSpaceifNull(f.readline().strip())
                        df['MOVEDATE'].append(MOVEDATE)
                    if data == u':토지이동사유관련지번':
                        REFJIBUN = self.returnSpaceifNull(f.readline().strip())
                        df['REFJIBUN'].append(REFJIBUN)
                    if data == u':사업시행신고구분코드':
                        SAUPCODE = self.returnSpaceifNull(f.readline().strip())
                        df['SAUPCODE'].append(SAUPCODE)
                    if data == u':사업시행지번호':
                        SAUPBUNHO = self.returnSpaceifNull(f.readline().strip())
                        df['SAUPBUNHO'].append(SAUPBUNHO)
                    if data == u':소유권변동원인구분코드':
                        OWNCHGCD = self.returnSpaceifNull(f.readline().strip())
                        df['OWNCHGCD'].append(OWNCHGCD)
                    if data == u':소유권변동일자':
                        OWNDATE = self.returnSpaceifNull(f.readline().strip())
                        df['OWNDATE'].append(OWNDATE)
                    if data == u':등록번호':
                        REGNUM = self.returnSpaceifNull(f.readline().strip())
                        df['REGNUM'].append(REGNUM)
                    if data == u':성명및명칭':
                        OWNER = self.returnSpaceifNull(f.readline().strip())
                        df['OWNER'].append(OWNER)
                    if data == u':주소':
                        ADDRESS = self.returnSpaceifNull(f.readline().strip())
                        df['ADDRESS'].append(ADDRESS)
                    if data == u':소유구분코드':
                        OWNGUBUNCD = self.returnSpaceifNull(f.readline().strip())
                        df['OWNGUBUNCD'].append(OWNGUBUNCD)
                    if data == u':공유구분코드':
                        GONGYU = self.returnSpaceifNull(f.readline().strip())
                        df['GONGYU'].append(GONGYU)
                    if data == u':도면구분':
                        REGMAP = self.returnSpaceifNull(f.readline().strip())
                        df['REGMAP'].append(REGMAP)
                    if data == u':용도지역':
                        YONGDO = self.returnSpaceifNull(f.readline().strip())
                        df['YONGDO'].append(YONGDO)
                    if data == u':국토계획법률':
                        LAW = self.returnSpaceifNull(f.readline().strip())
                        df['LAW'].append(LAW)
                    if data == u':다른법령':
                        OTHERLAW = self.returnSpaceifNull(f.readline().strip())
                        df['OTHERLAW'].append(OTHERLAW)
                    if data == u':토지이용규제':
                        REGULAR = self.returnSpaceifNull(f.readline().strip())
                        df['REGULAR'].append(REGULAR)
                    if data == u':시행령':
                        ORDER = self.returnSpaceifNull(f.readline().strip())
                        df['ORDER'].append(ORDER)
                    if data == u':공시지가가격(m2당)':
                        PRICE = self.returnSpaceifNull(f.readline().strip())
                        df['PRICE'].append(PRICE)
                    if data == u':원점코드':
                        WONJUM = self.code2wonjum(self.returnSpaceifNull(f.readline().strip()))
                        df['WONJUM'].append(WONJUM)
                    if data == u':종번':
                        LASTNUM = self.returnSpaceifNull(f.readline().strip())
                        df['LASTNUM'].append(LASTNUM)
                    if data == u'<필지E>':
                        pass
                    if data == u'<연속필지S>' or data == 'EOF':
                        break
        except Exception as e:
            print(e)

        etime = time.time()
        print(f'Time elapse: {etime-stime}')

        return df

    def __makeDataFrameFromShp(self, shp):
        """ shp를 DataFrame으로 변환"""
        return pd.read_file(shp).drop('geometry', axis=1)

    def cif2dataframe(self, cif):
        """ cif, shp를 DataFrame으로 변환"""
        if not os.path.exists(cif):
            return
        if cif.endswith('.cif'):
            return self.__makeDataFrameOBND(cif)
        return self.__makeDataFrameFromShp(cif)

    def makeShpCBND(self, cif):
        print(u"Transform Start: 연속지적")
        stime = time.time()
        shp = cif.replace(".cif", u"_연속지적.shp").replace(".Cif", u"_연속지적.shp")

        with shapefile.Writer(shp, encoding='euc-kr') as w:
            w.field('PNU', 'C', size='19')
            w.field('JIBUN', 'C')
            w.field('BCHK', 'C')

            rec = []
            PNU = JIBUN = BCHK = " "

            with open(cif, "r") as f:
                isStartCBND = False
                while 1:
                    data = f.readline().strip()

                    if not isStartCBND:
                        if data == u'<연속필지S>':
                            isStartCBND = True
                        else:
                            continue

                    if data == u'<연속필지S>':
                        data = f.readline().strip()
                        data = PNU = f.readline().strip()
                        rec.append(PNU)
                    if data == u':필계점':
                        parts = int(f.readline().strip())
                        pointcounts = []
                        for i in range(parts):
                            pointcounts.append(int(f.readline().strip()))
                            COORDS = [[] for i in range(parts)]
                        for part, counts in enumerate(pointcounts):
                            for i in range(counts):
                                y, x = f.readline().strip().split()
                                COORDS[part].append([float(x), float(y)])
                    if data == u':지목':
                        JIMOK = self.returnSpaceifNull(f.readline().strip())
                        JIBUN = self.pnu2jibun(PNU) + self.code2jimok(JIMOK)

                    if data == u'<연속필지E>':
                        w.poly(COORDS)
                        w.record(PNU, JIBUN, BCHK)
                    if data == u'<도곽S>' or data == 'EOF':
                        break
        print(u"Transform End: 연속지적")
        
        # 좌표계 설정: Korean_1985_Modified_Korea_Central_Belt, ESPG:5174
        self.set_crs(shp, 5174)

        etime = time.time()
        print(f'Time elapse: {etime-stime}')
        return shp

    def getlistitems(self):
        lst = [self.lstCifList.item(i).text() for i in range(self.lstCifList.count())]
        return lst

    def removeitems(self):
        selecteditems = self.lstCifList.selectedItems()
        for item in selecteditems:
            self.lstCifList.takeItem(self.lstCifList.row(item))

    def run(self):
        self.lblMessage.setText('')
        cifs = self.getlistitems()
        print(cifs)
        for cif in cifs:
            if self.option == 0:
                shp = self.makeShpOBND(cif)
            elif self.option == 1:
                shp = self.makeShpCBND(cif)
            else:
                shp = self.makeShpOBND(cif)
                shp = self.makeShpCBND(cif)
            self.lblMessage.setText(f'{cif}: 변환 완료!')


class CifInfoDialog(QWidget):
    def __init__(self, df):
        self.df = df
        print(self.df)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyCIF()
    myWindow.show()

    sys.exit(app.exec_())
