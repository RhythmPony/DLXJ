# 获取设备硬件信息

import wmi
import hashlib

ws = wmi.WMI()


# 获取主板序列号
def get_baseboard_serial():
    bbs = ws.Win32_BaseBoard()
    bs = bbs[0].SerialNumber
    return bs


# 获取处理器ID
def get_processor_id():
    cpus = ws.Win32_Processor()
    PId = cpus[0].ProcessorId
    return PId


# 获取磁盘驱动ID
def get_disk_drive():
    dds = ws.Win32_DiskDrive()
    DId = dds[0].DeviceID
    return DId


# 获取MAC地址
def get_mac_address():
    nac = ws.Win32_NetworkAdapterConfiguration()
    for n in nac:
        if n.MACAddress:
            return n.MACAddress
            break


# 使用主板序列号+MAC地址+key加密
def crypto():
    key = '_shakunage_3000_'
    rowStr = get_baseboard_serial() + get_disk_drive() + key
    targetStr = hashlib.md5()
    targetStr.update(rowStr.encode())
    return targetStr.hexdigest()


if __name__ == '__main__':
    with open('request.code', 'w', encoding='utf-8') as request:
        request.write(crypto())
        request.close()
    print('--注册文件已生成--')
