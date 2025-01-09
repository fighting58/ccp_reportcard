from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QPushButton
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QRect
from PySide6.QtGui import QPixmap, QScreen
import sys



class vworldMapViewer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
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

        html = """

        <html>
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
        <title>Marker</title>
        <!-- API key를 포함하여 브이월드 API URL을 지정하여 호출끝  -->
        <script type="text/javascript" src="https://map.vworld.kr/js/vworldMapInit.js.do?version=2.0&apiKey=D73040C7-5E55-32F2-80F5-BDF30FD49608"></script>

        </head>

        <body>
        <div id="vmap" style="width:100%;height:100%;left:0px;top:0px"></div>
        <!--
        <div id="buttons">
        <button type="button" onclick="javascript:addMarkerLayer();" >마커입력</button>
        <button type="button" onclick="javascript:checkMarkerParam();" >마커입력오류</button>
        <button type="button" onclick="javascript:hideMarker();" >마커숨기기</button>
        <button type="button" onclick="javascript:showMarker();" >마커보기</button>
        <button type="button" onclick="javascript:hideAllMarker();" >마커전체숨기기</button>
        <button type="button" onclick="javascript:showAllMarker();" >마커전체보기</button>
        <button type="button" onclick="javascript:removeMarker();" >마커삭제</button>
        <button type="button" onclick="javascript:removeAllMarker();" >마커전체삭제</button>
        <button type="button" onclick="javascript:showPopup();" >마커팝업열기</button>
        <button type="button" onclick="javascript:hidePopup();" >마커팝업닫기</button>
        <input type="text" id="param" value="" size="20"/>  
        </div>
        -->
        
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
            x : 126.24,
            y : 37.4,
            epsg : "EPSG:4326",
            title : '테스트마커1',
            contents : '테스트마커1 본문내용',
            text : {
                offsetX: 0.5, //위치설정
                offsetY: 20,   //위치설정
                font: '12px Calibri,sans-serif',
                fill: {color: '#000'},
                stroke: {color: '#fff', width: 6},
                text: '테스트마커1'
            },
            attr: {"id":"maker01","name":"속성명1"}	
        };
        markerLayer.addMarker(vw.ol3.markerOption);

        vw.ol3.markerOption = {
            x : 14164292.00853613,
            y : 4495009.258626321,
            epsg : "EPSG:900913",
            title : '테스트마커2',
            contents : '테스트마커2 본문내용<br>테스트마커2 본문내용',

            text : {
                offsetX: 0.5, //위치설정
                offsetY: 20,   //위치설정
                font: '12px Calibri,sans-serif',
                fill: {color: '#000'},
                stroke: {color: '#fff', width: 2},
                text: '테스트마커2'
            },
            attr: {"id":"maker02","name":"속성명2"}	
        };
        markerLayer.addMarker(vw.ol3.markerOption);

        vw.ol3.markerOption = {
            x : 14129709.590359,
            y : 4442313.7639686,
            epsg : "EPSG:3857",
            title : '브이월드로 가자',
            contents : "<a href='//map.vworld.kr' target='_blank'>브이월드로 GOGOGO</a><br><br><a href='//dev.vworld.kr' target='_blank'>개발자센터 GOGOGO</a>", 
            text : {
                offsetX: 0.5, //위치설정
                offsetY: 20,   //위치설정
                font: '12px Calibri,sans-serif',
                fill: {color: '#000'},
                stroke: {color: '#fff', width: 2},
                text: '테스트마커3'
            },
            attr: {"id":"maker03","name":"속성명3"}
        };
        markerLayer.addMarker(vw.ol3.markerOption);
        }

        function checkMarkerParam() {
        if (markerLayer == null) {
            alert("마커레이어가 생성되지 않았습니다.n마커입력버튼을 먼저 실행하십시요.");
            return false;
        }
        vw.ol3.markerOption = {
            x: 283256.233,
            y: 556675.577,
            epsg : "EPSG:5186",
            title : '네이버좌표계',
            contents : '덕수초등학교', 
            text : {
                offsetX: 0.5, //위치설정
                offsetY: 20,   //위치설정
                font: '12px Calibri,sans-serif',
                fill: {color: '#000'},
                stroke: {color: '#fff', width: 2},
                text: '테스트마커4'
            },
            attr: {"id":"maker04","name":"속성명4"}
        };
        markerLayer.addMarker(vw.ol3.markerOption);
        }

        function isSelectMarker(){
        if (markerLayer == null) {
            alert("마커레이어가 생성되지 않았습니다.n마커입력버튼을 먼저 실행하십시요.");
            return false;
        } else {
            if (this.markerLayer.getSource().getFeatures().length < 1) {
            alert("생성된 마커가 없습니다.");
            return false;
            } else {
            if($('#param').val() == ''){
            alert("선택된 마커가 없습니다. 마커에 마우스를 올리세요.");
            return false;
            }else{
            return true;
            }
            }
        }
        }
        function showPopup(){
        if(isSelectMarker()){
            this.markerLayer.showPop(selectMarker);
        }
        }
        function hidePopup(){
        if(isSelectMarker()){
            this.markerLayer.hidePop(selectMarker);
        }
        }
        
        function hideMarker() {
        if(isSelectMarker()){
            this.markerLayer.hideMarker(selectMarker);
        }
        }
        function showMarker() {
        if(isSelectMarker()){
            this.markerLayer.showMarker(selectMarker);
            $('#param').val('');
        }
        }

        function hideAllMarker() {
        if(markerLayer == null){
            alert("마커레이어가 생성되지 않았습니다.n마커입력버튼을 먼저 실행하십시요.");
        } else {
            this.markerLayer.hideAllMarker();
        }
        }

        function showAllMarker() {
        if(markerLayer == null){
            alert("마커레이어가 생성되지 않았습니다.n마커입력버튼을 먼저 실행하십시요.");
        } else {
            this.markerLayer.showAllMarker();
        }
        }

        function removeMarker() {
        if(isSelectMarker()){
            var features = this.markerLayer.getSource().getFeatures();
            for(var i=0; i<features.length; i++){
            if($('#param').val() == features[i].get('id')){
            this.markerLayer.removeMarker(selectMarker);
            $('#param').val('');
            selectMarker = null;
            }
            }
        }
        }

        function removeAllMarker() {
        if(markerLayer == null){
            alert("마커레이어가 생성되지 않았습니다.n마커입력버튼을 먼저 실행하십시요.");
        } else {
            this.markerLayer.removeAllMarker();
        }
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
            move(126.24, 37.4, 5);
        };
        </script>
        </body>
        </html>
        """

        self.web_view.setHtml(html)

    def capture_screen(self):
        screen = QScreen.grabWindow(self.windowHandle().screen(), self.winId(), 20, 20, 800, 600)
        screen.save("123.png", "png")


if __name__ == "__main__":  
    app = QApplication(sys.argv)
        
    view = vworldMapViewer()
    view.exec()
