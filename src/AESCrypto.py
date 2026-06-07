import base64
from Cryptodome.Cipher import AES
from Cryptodome import Random
import pandas as pd


class AESCipher:
    def __init__(self):
        '''
        CBC加密需要一个十六位的key(密钥)和一个十六位iv(偏移量)
        '''
        self.key = self.check_key('_shakunage_3000_')
        # 数据块的大小  16位
        self.BS = 16
        # CBC模式 相对安全 因为有偏移向量 iv 也是16位字节的
        self.mode = AES.MODE_CBC
        # 填充函数 因为AES加密是一段一段加密的  每段都是BS位字节，不够的话是需要自己填充的
        self.pad = lambda s: s + (self.BS - len(s.encode()) % self.BS) * chr(self.BS - len(s.encode()) % self.BS)
        # 将填充的数据剔除
        self.unpad = lambda s: s[:-ord(s[len(s) - 1:])]

    @staticmethod
    def check_key(key):
        '''
        检测key的长度是否为16,24或者32bytes的长度
        '''
        try:
            if isinstance(key, bytes):
                assert len(key) in [16, 24, 32]
                return key
            elif isinstance(key, str):
                assert len(key.encode()) in [16, 24, 32]
                return key.encode()
            else:
                raise Exception(f'密钥必须为str或bytes,不能为{type(key)}')
        except AssertionError:
            print('输入的长度不正确')

    @staticmethod
    def check_data(data):
        '''
        检测加密的数据类型
        '''
        if isinstance(data, int):
            data = str(data)
        elif isinstance(data, bytes):
            data = data.decode()
        elif isinstance(data, str):
            pass
        else:
            raise Exception(f'加密的数据必须为str或bytes,不能为{type(data)}')
        return data

    def encrypt(self, raw):
        raw = self.check_data(raw)
        raw = self.pad(raw).encode()
        # 随机获取iv
        iv = Random.new().read(AES.block_size)
        # 定义初始化
        cipher = AES.new(self.key, self.mode, iv)
        # 此处是将密文和iv一起 base64 解密的时候就可以根据这个iv来解密
        return base64.b64encode(iv + cipher.encrypt(raw)).decode()

    def decrypt(self, enc):
        # 先将密文进行base64解码
        enc = base64.b64decode(enc)
        # 取出iv值
        iv = enc[:self.BS]
        # 初始化自定义
        cipher = AES.new(self.key, self.mode, iv)
        # 返回utf8格式的数据
        return self.unpad(cipher.decrypt(enc[self.BS:])).decode()


if __name__ == "__main__":
    aes = AESCipher()
    df = pd.DataFrame(data=[13462403256, 13462403286], columns=['id'])
    print(df)
    df['id'] = df['id'].map(aes.encrypt)
    print(df)
    df['id'] = df['id'].map(aes.decrypt)
    print(df)
