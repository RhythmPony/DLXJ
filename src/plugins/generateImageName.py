import os.path
import sys


def generate_image_name(params_dict: dict) -> tuple:
    sys.path.append("..")
    from src.utils import get_option
    line_name = params_dict["lineEdit2_text"]
    line_code = params_dict["lineEdit3_text"]
    defects_part = params_dict["rb1_text"]
    defects_level = params_dict["rb2_text"].split(',')[0]
    defects_type = params_dict["cb1_text"]
    defects_description = params_dict["cb2_text"]
    file_name = '_'.join([line_code, defects_part, defects_level, defects_type, defects_description])
    dir_name = get_option("file", "image_saving_directory", "images")
    dir_name = os.path.normcase(os.path.join(dir_name, line_name))
    return dir_name, file_name
