# -*- coding: utf-8 -*-
import shapefile
import os
import geopandas as gpd
import tempfile

class CifGeoDataFrame:
    def __init__(self, cif:str):
        self.cif = cif

    def returnSpaceifNull(self, s):
        return s if len(s) > 0 else ' '

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

    def convert_to_geodataframe(self):
        cif_basename = os.path.basename(self.cif)

        with tempfile.TemporaryDirectory() as temp_dir:
            shp = cif_basename.lower().replace('.cif', "_temp.shp")
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
                    with open(self.cif, "r") as f:
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
            
            gdf = gpd.read_file(shp)
        return gdf
    
    def __call__(self):
        return self.convert_to_geodataframe()
