import hashlib
import datetime
from AESCrypto import AESCipher


def register():
    path = r'F:\\request.code'
    with open(path, 'r+') as r:
        rowStr = r.readline().strip()
        local_code = hashlib.md5()
        local_code.update((rowStr + '_shakunage_3000_').encode())
        local_code = local_code.hexdigest()
        expire = AESCipher().encrypt(
            (datetime.datetime.now() + datetime.timedelta(days=60)).strftime('%Y-%m-%d %H:%M:%S'))
    with open(r'F:\\register.auth', 'w+') as r:
        r.write('register_code:' + local_code + '\nexpire:' + expire)


if __name__ == '__main__':
    register()
