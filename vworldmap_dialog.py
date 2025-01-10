from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QScreen
from PySide6.QtCore import QUrl, Signal
import sys
import os
from __api_key import VWorldApiKey
from pyproj import Transformer

class VWorldPintMapHtmlCreator:
    def __init__(self, x, y, **kargs):
        self.x = x
        self.y = y
        self.api_key = kargs.get("api_key", VWorldApiKey().KEY)
        self.name = kargs.get("name", "POINT")
        self._html_template = """
            <html>
            <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge" />
            <title>Marker</title>
            <!-- API key를 포함하여 브이월드 API URL을 지정하여 호출끝  -->
            <script type="text/javascript" src="https://map.vworld.kr/js/vworldMapInit.js.do?version=2.0&apiKey=%%VWORLD_API_KEY%%"></script>
            </head>

            <body>
            <div id="vmap" style="width:100%;height:100%;left:0px;top:0px"></div>
          
            <script type="text/javascript">
            var vmap;
            var selectMarker;
            
            vw.ol3.MapOptions = {
                basemapType: vw.ol3.BasemapType.PHOTO
                , controlDensity: vw.ol3.DensityType.EMPTY
                , interactionDensity: vw.ol3.DensityType.BASIC
                , controlsAutoArrange: true
                , homePosition: vw.ol3.CameraPosition
                , initPosition: vw.ol3.CameraPosition
            }; 
                
            vmap = new vw.ol3.Map("vmap",  vw.ol3.MapOptions); 
            
            var markerLayer;
            function addMarkerLayer() {
                if (markerLayer != null) {
                    vmap.removeLayer(markerLayer);
                    }
                    markerLayer = new vw.ol3.layer.Marker(vmap);
                    vmap.addLayer(markerLayer);
                }

            function addMarker() {
                vw.ol3.markerOption = {
                    x : %%X%%,
                    y : %%Y%%,
                    epsg : "EPSG:4326",
                    title : '%%NAME%%',
                    contents : '%%X%%, %%Y%%',
                    iconUrl : 'https://map.vworld.kr/images/etrimap/umap/pointer/ico-type2-05.png',
                    text : {
                        offsetX: 0.5, //위치설정
                        offsetY: 10,   //위치설정
                        font: '16px Calibri,sans-serif',
                        fill: {color: '#000'},
                        stroke: {color: '#fff', width: 6},
                        text: '%%NAME%%'
                        },
                    attr: {"id":"maker01","name":"속성명1"}	
                };
            markerLayer.addMarker(vw.ol3.markerOption);
            }

            function move(x,y,z){
                var _center = [ x, y ];
                
                var z = z;
                var pan = ol.animation.pan({
                    duration : 0,
                    source : (vmap.getView().getCenter())
                });
                vmap.beforeRender(pan);
                vmap.getView().setCenter(ol.proj.transform(_center, 'EPSG:4326', 'EPSG:3857'));
                setTimeout("fnMoveZoom()", 0);
            }
                
            function fnMoveZoom() {
                zoom = vmap.getView().getZoom();
                if (16 > zoom) {
                    vmap.getView().setZoom(18.5);    <!-- 7 <= zoom <= 19 -->
                }                
            }
                
            window.onload = function() {
                addMarkerLayer();
                addMarker();
                move(%%X%%, %%Y%%, 5);
            };
            </script>
            </body>
            </html>
            """
    @property
    def html(self): 
        return self._html_template.replace("%%VWORLD_API_KEY%%", self.api_key).replace("%%X%%", self.x).replace("%%Y%%", self.y).replace("%%NAME%%", self.name)


class VWorldMapViewer(QDialog):
    save_sat_image_request = Signal(int, str)

    def __init__(self, x, y, parent=None, **kargs):
        super().__init__(parent)
        self.x = x
        self.y = y
        self.name = kargs.get("name", "POINT")
        self.path = kargs.get("path", '.')
        self.row = kargs.get("row", None)
        self.parent = parent
        self.apply_transform = kargs.get("apply_transform", False)
        if self.apply_transform:
            self.x, self.y = self.transform(reverse=True) # 세계좌표를 경위도 좌표로 변환

        self.setWindowTitle("vworldMapViewer")
        self.resize(420, 410)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self) 
        self.web_view = QWebEngineView(self) 
        layout.addWidget(self.web_view)

        # Add a button to capture the screen
        self.capture_button = QPushButton("Capture Screen", self)
        self.capture_button.clicked.connect(self.capture_screen)
        layout.addWidget(self.capture_button)
        layout.setContentsMargins(0, 0, 0, 0)
        self.web_view.setHtml(VWorldPintMapHtmlCreator(str(self.x), str(self.y), name=self.name).html)

    def transform(self, **kargs):
        """좌표 변환
        좌표 변환을 위해 pyproj.Transformer 클래스를 사용하며 기본적으로 경위도좌표를 세계측지계(중부)로 변환한다.

        Args:
            x (float): epsg:4326의 경우 경도
            y (float): epsg:4326의 경우 위도
        kargs:
            from_epsg (str, optional): 변환전 좌표 ESPG. Defaults to "EPSG:4326".
            to_epsg (str, optional): 변환후 좌표 ESPG. Defaults to "EPSG:5186".
            revese (bool, optional): 역변환 여부. Defaults to False.

        Returns:
            tuple(float, float): 변환된 좌표
        """
        from_epsg = kargs.get("from_espg", "EPSG:4326")
        to_epsg = kargs.get("to_espg", "EPSG:5186")
        reverse = kargs.get("reverse", False)

        if reverse:
            from_epsg, to_epsg = to_epsg, from_epsg

        transformer = Transformer.from_crs(from_epsg, to_epsg, always_xy=True)

        return transformer.transform(self.x, self.y)

    def capture_screen(self):
        screen = QScreen.grabWindow(self.windowHandle().screen(), self.winId(), 10, 10, 400, 300)
        filename = f"{self.name}_위성.png"
        save_path = os.path.join(self.path, filename)
        screen.save(save_path, "png")
        if self.row is not None:
            if self.parent is not None:
                print(self.parent)
                self.parent.show_modal("success", parent=self.web_view, title=" Saving Success", description=f"위성사진이 성공적으로 저장되었습니다.\n{filename}")
            self.save_sat_image_request.emit(self.row, filename)


if __name__ == "__main__":  
    app = QApplication(sys.argv)
        
    view = VWorldMapViewer(221115.187, 515152.230, name="10230", apply_transform=True)
    view.exec()
