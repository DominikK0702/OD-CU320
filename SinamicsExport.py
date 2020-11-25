import time
import requests
import subprocess
from loguru import logger


def get_last_trace(ip, csvfilepath, user='SINAMICS', passw=''):
    cookies = {
        'siemens_automation_language': '0',
        'siemens_ad_session'         : '',
    }
    headers = {
        'Connection'     : 'keep-alive',
        'Accept'         : 'application/json, text/plain, */*',
        'User-Agent'     : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
        'Content-type'   : 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin'         : f'http://{ip}',
        'Referer'        : f'http://{ip}/login',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Pragma'         : 'no-cache',
        'Cache-Control'  : 'no-cache',
        'Accept-Encoding': 'gzip, deflate',
        'HOST'           : '169.254.11.22'
    }

    data = {
        'Login'      : user,
        'Password'   : passw,
        'Redirection': '/index.mwsl'
    }

    try:
        response = requests.post(f'http://{ip}/FormLogin', headers=headers, cookies=cookies, data=data, verify=False)
        if response.status_code == 200:
            cookies['siemens_ad_session'] = response.headers.get('set-cookie').split(';')[0][19:]
            headers['Referer'] = f'http://{ip}/login'
            logger.debug("Sinamics login success")
        else:
            logger.error("Sinamics login failed")

        res = requests.get(f'http://{ip}/STATUSAPP?LOGGEDINUSER&_={int(time.time() * 1000)}', headers=headers,
                           cookies=cookies)
        if res.status_code == 200:
            headers['Referer'] = f'http://{ip}/diagnostics/tracefiles'
            logger.debug("Sinamics login check success")
        else:
            logger.error("Sinamics login check failed")

        res = requests.get(f'http://{ip}/PAGELOADER?page=tracefile', headers=headers,
                           cookies=cookies)
        if res.status_code == 200:

            ts = max([int(i[1]) for i in res.json()])

            tracefile = [i[0] for i in res.json() if int(i[1]) == ts].pop()
            headers = {
                'Upgrade-Insecure-Requests': '1',
                'User-Agent'               : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36'
            }
            logger.debug("Sinamics loading tracefiles success")

            res = requests.get(f'http://{ip}/DRVTRACEFILEAPP/{tracefile}', headers=headers, cookies=cookies,
                               allow_redirects=True)

            if res.status_code == 200:
                with open('./export/tmp.ACX.GZ', 'wb') as f:
                    f.write(res.content)

                subprocess.call(
                    ['./bin/Convert_SINAMICS_trace_CSV.exe', './export/tmp.ACX.GZ', '-sep', 'SEMICOLON', '-out',
                     csvfilepath])
                logger.debug("Sinamics converting tracefile success")
                return csvfilepath
            else:
                logger.error("Sinamics converting tracefile failed")
        else:
            logger.error("Sinamic loading tracefiles failed")
    except Exception as e:
        logger.error(f"Error exporting trace from controller {ip}")
        return
