# 自动填充文本 插件
import logging
import os
import re


def auto_fill(file_name: str) -> list[str]:
    text1 = ""
    text2 = ""
    text3 = ""
    text4 = ""
    text5 = ""
    try:
        text2 = re.search(r'\w+(?=#\d+)', file_name)[0]
        text3 = re.search(r'#[\d-]+[\d+-]*', file_name)[0]
        if text2 and text3:
            text5 = os.path.basename(file_name)
            text1 = '[LEVEL][COUNT]_' + text2 + '_' + text3
        text4 = ""
    except Exception as e:
        logging.warning(str(e))
    finally:
        filling_texts = [text1, text2, text3, text4, text5]
        return filling_texts
