from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtGui import QScreen
from PySide6.QtCore import QUrl
import sys
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
            
            vmap.on('pointermove', function(evt) {
                var feature = vmap.forEachFeatureAtPixel(evt.pixel, function(feature,layer) {
                    if (layer != null && layer.className == 'vw.ol3.layer.Marker') {
                    $('#param').val('');
                    $('#param').val(feature.get('id'));
                    selectMarker = feature;
                    } else {
                    return false;
                    }
                });
            });
            
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
                    vmap.getView().setZoom(20);
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


class vworldMapViewer(QDialog):
    def __init__(self, x, y, point_name, parent=None):
        super().__init__(parent)
        self.x = x
        self.y = y
        self.name = point_name
        self.setWindowTitle("vworldMapViewer")
        self.resize(840, 720)
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

        print(VWorldPintMapHtmlCreator(str(self.x), str(self.y), name=self.name).html)
        self.web_view.setHtml(VWorldPintMapHtmlCreator(str(self.x), str(self.y), name=self.name).html)

    def transform(self, x, y, **kargs):
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
        reverse = kargs.get("revese", False)

        if reverse:
            from_epsg, to_epsg = to_epsg, from_epsg

        transformer = Transformer.from_crs(from_epsg, to_epsg, always_xy=True)

        return transformer.transform(x, y)

    def capture_screen(self):
        screen = QScreen.grabWindow(self.windowHandle().screen(), self.winId(), 20, 20, 800, 600)
        screen.save("123.png", "png")


if __name__ == "__main__":  
    app = QApplication(sys.argv)
        
    view = vworldMapViewer(127.23795321951091, 37.23529265431432, "10230")
    view.exec()
