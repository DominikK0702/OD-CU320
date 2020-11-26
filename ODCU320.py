import requests
import time
import subprocess
import os


class CU320:
    def __init__(self, ip='169.254.11.22', user='SINAMICS', passw=''):
        self.ip = ip
        self.username = user
        self.password = passw
        self.session = requests.Session()
        self.init_cookies()
        self.init_headers()
        self.data = {
            'Login'      : self.username,
            'Password'   : self.password,
            'Redirection': '/index.mwsl'
        }
        self.token = None

    def __repr__(self):
        return f"IP: {self.ip}"

    def init_cookies(self):
        self.session.cookies.set('siemens_automation_language', '0')

    def init_headers(self):
        self.session.headers['Connection'] = 'keep-alive'
        self.session.headers['Accept'] = 'application/json, text/plain, */*'
        self.session.headers[
            'User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
        self.session.headers['Content-type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        self.session.headers['Origin'] = f'http://{self.ip}'
        self.session.headers['Referer'] = f'http://{self.ip}/login'
        self.session.headers['Accept-Language'] = 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7'
        self.session.headers['Pragma'] = 'no-cache'
        self.session.headers['Cache-Control'] = 'no-cache'
        self.session.headers['Accept-Encoding'] = 'gzip, deflate'
        self.session.headers['HOST'] = '169.254.11.22'

    def login(self):
        response = self.session.post(f"http://{self.ip}/FormLogin", data=self.data)
        self.session.headers['Referer'] = f'http://{self.ip}/login'
        return response.status_code == 200

    def logout(self):
        response = self.session.post(f"http://{self.ip}/FormLogin?LOGOUT", data={
            'MultiUseToken': self.token,
            'Redirection'  : '/index.mwsl'
        })
        return response.status_code == 200

    def check_logged_in(self):
        response = self.session.get(f"http://{self.ip}/STATUSAPP?LOGGEDINUSER&_={int(time.time() * 1000)}")
        self.session.headers['Referer'] = f'http://{self.ip}/diagnostics/tracefiles'
        if response.status_code == 200:
            self.token = response.json().get('token')
            time.sleep(1)
            return True

    def get_last_tracefile_name(self):
        response = self.session.get(f"http://{self.ip}/PAGELOADER?page=tracefile")

        if response.status_code == 200:
            tracefiles = response.json()
            ts = max([int(i[1]) for i in tracefiles])
            newest_tracefile = [i[0] for i in tracefiles if int(i[1]) == ts].pop()
            return newest_tracefile

    def get_tracefile(self, tracename, out_dir):
        response = self.session.get(f'http://{self.ip}/DRVTRACEFILEAPP/{tracename}', allow_redirects=True)
        if response.status_code == 200:
            with open(out_dir + 'TMP_TRACE.ACX.GZ', 'wb') as f:
                f.write(response.content)
            return out_dir + 'TMP_TRACE.ACX.GZ'

    def convert_tracefile_to_csv(self):
        input_file_name = '.\\in\\tmp.acx.gz'
        output_file_name = '.\\out\\trace.csv'
        sts = subprocess.Popen(os.path.join(os.getcwd(), "bin", "Convert_SINAMICS_trace_CSV.exe")
                               + f" {input_file_name} -out {output_file_name} -sep SEMICOLON", shell=True).wait()
        return sts == 0
