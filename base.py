import os
import sys

BASE_DIR = os.path.normcase(os.path.abspath(os.getcwd()))
sys_config_path = r"config.ini"
sys.path.append(BASE_DIR)
