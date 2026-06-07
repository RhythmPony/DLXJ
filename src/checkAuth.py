import datetime
import hashlib
import json
import logging
import time

import requests
import win32api
import win32con

from src.AESCrypto import AESCipher

from src.getHardwareInfo import crypto


def is_authed(auth_info):
    try:
        local_code = hashlib.md5()
        local_code.update((crypto() + '_shakunage_3000_').encode())
        local_code = local_code.hexdigest()
        current_time = get_beijing_time()
        expire_time = datetime.datetime.strptime(AESCipher().decrypt(auth_info["expire"]),
                                                 '%Y-%m-%d %H:%M:%S')
        last_time = datetime.datetime.strptime(AESCipher().decrypt(auth_info["last_login_time"]),
                                               '%Y-%m-%d %H:%M:%S')
        if local_code == auth_info["register_code"]:
            if last_time <= current_time <= expire_time:
                return True
    except Exception as e:
        return False


def get_beijing_time():
    try:
        url = 'https://beijing-time.org/'
        request_result = requests.get(url=url)
        if request_result.status_code == 200:
            headers = request_result.headers
            net_date = headers.get("date")
            gmt_time = time.strptime(net_date[5:25], "%d %b %Y %H:%M:%S")
            bj_timestamp = int(time.mktime(gmt_time) + 8 * 60 * 60)
            return datetime.datetime.fromtimestamp(bj_timestamp)
    except Exception as e:
        return datetime.datetime.now()


def get_sys_info():
    try:
        with open("LICENSE", "r") as lcs:
            auth_info = json.loads(lcs.read())
        return auth_info
    except Exception as e:
        logging.warning(str(e))
        return -1


def update_sys_info(auth_info):
    auth_info["last_login_time"] = AESCipher().encrypt(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    win32api.SetFileAttributes("LICENSE", win32con.FILE_ATTRIBUTE_NORMAL)
    with open("LICENSE", "w") as lcs:
        lcs.write(json.dumps(auth_info, indent=4))
    win32api.SetFileAttributes("LICENSE", win32con.FILE_ATTRIBUTE_HIDDEN)
