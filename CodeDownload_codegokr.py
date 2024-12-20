import requests
import zipfile
import os
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
import ssl

class SSLAdapter(HTTPAdapter):
    """An HTTPAdapter that uses a custom SSL context."""

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
        """Initialize the pool manager with a custom SSL context."""
        kwargs['ssl_context'] = self.ssl_context
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            **kwargs
        )

    def proxy_manager_for(self, proxy, **kwargs):
        """Ensure the custom SSL context is used for proxy connections."""
        kwargs['ssl_context'] = self.ssl_context
        return super().proxy_manager_for(proxy, **kwargs)


class CodeGoKr:
    def __init__(self):
        self._db_name = "법정동코드 전체자료.txt"
        self.__url = 'https://www.code.go.kr/etc/codeFullDown.do'
        self.__header = {'Host': 'www.code.go.kr',
                        'Connection': 'keep-alive',
                        'Content-Length': '221',
                        'Cache-Control': 'max-age=0',
                        'sec-ch-ua': '" Not_A Brand";v="24", "Chromium";v="131", "Google Chrome";v="131"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': "Windows",
                        'Upgrade-Insecure-Requests': '1',
                        'Origin': 'https://www.code.go.kr',
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Sec-Fetch-Site': 'same-origin',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-User': '?1',
                        'Sec-Fetch-Dest': 'iframe',
                        'Referer': 'https://www.code.go.kr/stdcode/regCodeL.do',
                        'Accept-Encoding': 'gzip, deflate, br, zstd',
                        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,de;q=0.5,es;q=0.4,zh-CN;q=0.3,zh-TW;q=0.2,zh;q=0.1',
                        'Cookie': 'SCOUTER=xaooujbbtlno6; JSESSIONID=wc+qr8I6QUsTIBnzOoxEsyMP.CODROOTserver2; codeCount=20241220'
                        }
        self.__payload = {'cPage': '1', 
                        'regionCd_pk': '',
                        'chkWantCnt': '',
                        'reqSggCd': '',
                        'reqUmdCd': '',
                        'reqRiCd': '',
                        'searchOk': '',
                        'codeseId': '법정동코드',
                        'pageSize': '10',
                        'regionCd': '',
                        'locataddNm': '',
                        'sidoCd': '*',
                        'sggCd': '*',
                        'umdCd': '*',
                        'riCd':'*',
                        'disuseAt': '0',
                        'stdate': '',
                        'enddate': ''
                        }
        self.__work_path = "./"
        self.filename = self.__work_path + '법정동코드 전체자료.zip'

        # Create a custom SSL context and apply it to the session
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers("DEFAULT:@SECLEVEL=1")
        self.session = requests.Session()
        adapter = SSLAdapter(ssl_context=ssl_context)
        self.session.mount('https://', adapter)

    @property
    def dbName(self):
        if self.is_exists_db():
            return self._db_name
        return None

    def __getzip(self):
        for attempt in range(6):
            try:
                response = self.session.post(
                    self.__url,
                    headers=self.__header,
                    data=self.__payload,
                    stream=True
                )

                if response.status_code == 200:
                    print("Downloading zip file...")

                with open(self.filename, "wb") as zip:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            zip.write(chunk)
                print(f"Download successful on attempt {attempt + 1}")
                return
            except requests.exceptions.ConnectionError as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == 5:
                    raise Exception("Max retries exceeded.")

    def __unzip(self, source_file, dest_path):
        name = ''
        with zipfile.ZipFile(source_file, 'r') as zf:
            zip_info = zf.infolist()
            for member in zip_info:
                try:
                    member.filename = member.filename.encode('cp437').decode('euc-kr', 'ignore')
                    zf.extract(member, dest_path)
                except:
                    print(source_file)
                    raise Exception('Extraction error')
            name = zip_info[0].filename
        return name

    def get_db(self):
        self.__getzip()
        if os.path.exists(self.filename):
            self.is_exists_db(remove=True)
            textfile = self.__unzip(self.filename, self.__work_path)
            os.remove(self.filename)
            print(f"{textfile}: 생성 성공")
            self._db_name = textfile
            return self._db_name
        else:
            print("Zip file not found.")
            return os.path.join(self.__work_path, textfile)

    def is_exists_db(self, remove=False):
        if os.path.exists(self._db_name):
            if remove:
                os.remove(self._db_name)
                return False
            return True
        return False

if __name__ == "__main__":
    d = CodeGoKr()
    dbfile = d.get_db()
    print(dbfile)