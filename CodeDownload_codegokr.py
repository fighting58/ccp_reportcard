import requests
import zipfile
import os

class CodeGoKr:
    def __init__(self):
        self._db_name = "법정동코드 전체자료.txt"
        self.__url ='https://www.code.go.kr/etc/codeFullDown.do?codeseId=00002'

        self.__header = {'Host': 'www.code.go.kr',
                        'Connection': 'keep-alive',
                        'Content-Length': '14',
                        'Cache-Control': 'max-age=0',
                        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': "Windows",
                        'Upgrade-Insecure-Requests': '1',
                        'Origin': 'https://www.code.go.kr',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-User': '?1',
                        'Sec-Fetch-Dest': 'iframe',
                        'Referer': 'https://www.code.go.kr/stdcodesrch/codeAllDownloadL.do',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'ko,en-US;q=0.9,en;q=0.8',
                        'Cookie': 'codeCount=20220103; JSESSIONID=eP5H5+3-UnWLRN3xgOOT4eU7.CODROOTserver1; clientid=040011633063; GPKISecureWebSession=gsrmGc1RCWu3snviavdB'
                        }

        self.__payload = {'codeseld': '00002'}
        self.__work_path = "./"
        self.filename = self.__work_path + '법정동코드 전체자료.zip'
        self.__tries = 0
    
    @property
    def dbName(self):
        if self.is_exists_db():
            return self._db_name
        return None

    def __getzip(self):
        """ 행정표준코드관리시스템에 접속하여 법정동코드를 다운로드 """
        flag = 0
        try:
            response = requests.post(self.__url, headers=self.__header, data=self.__payload, stream=True)
            response.encoding = response.apparent_encoding
            self.__tries += 1
            flag = 1
        except requests.exceptions.ConnectionError as e:
            print(e)
        finally:
            if flag:
                with open(self.filename, "wb") as zip:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            zip.write(chunk)
            # 5회 초과 다운로드 실패시 메시지 생성
            elif self.__tries > 5:
                print("Connection Fail - Try Again!!")
            # 5회 이하의 경우, 재귀
            else:
                print(f'{self.__tries}회 연결 실패.')
                self.__getzip()

    def __unzip(self, source_file, dest_path):
        """압축 해제 후 그 첫번째 파일명을 반환"""

        name = ''
        with zipfile.ZipFile(source_file, 'r') as zf:
            zip_info = zf.infolist()
            for member in zip_info:
                try:
                    # print(member.filename.encode('cp437').decode('euc-kr', 'ignore'))
                    member.filename = member.filename.encode('cp437').decode('euc-kr', 'ignore')
                    zf.extract(member, dest_path)
                except:
                    print(source_file)
                    raise Exception('what?!')
            name = zip_info[0].filename
        return name

    def get_db(self):
        """ 일괄 처리 """
        self.__getzip()     

        if os.path.exists(self.filename):
            self.is_exists_db(remove=True)
            textfile = self.__unzip(self.filename, self.__work_path)
            if not textfile:
                print("DB 생성에 실패하였습니다.")
                return
            # 성공하면 zip파일 삭제
            os.remove(self.filename)
            print(f"{textfile}: 생성 성공")
            # 파일명 반환
            return os.path.join(self.__work_path, textfile)
        return
    
    def is_exists_db(self, remove=False):        
        if os.path.exists(self._db_name):
            if remove:
                os.remove(self._db_name)
                return False
            return True
        return False

        


if __name__ == "__main__":
    d = CodeGoKr()
    d.get_db()
