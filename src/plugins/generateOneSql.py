def generate_one_sql(params_list, params_dict):
    if len(params_list) == 1:
        img_path_1 = params_list[0]
        img_path_2 = ""
    elif len(params_list) == 2:
        img_path_1 = params_list[0]
        img_path_2 = params_list[1]
    else:
        return
    table_name = params_dict["rb2_text"].split(',')[-1]
    rid = None
    line_name = params_dict["lineEdit2_text"]
    line_code = params_dict["lineEdit3_text"]
    inspection_method = params_dict["lineEdit4_text"]
    defects_parts = params_dict["rb1_text"]
    defects_level = params_dict["rb2_text"].split(',')[0]
    inspection_date = params_dict["dateEdit_text"]
    defects_type = params_dict["cb1_text"]
    defects_description = params_dict["cb2_text"]
    img_count = len(params_list)
    source_image = params_dict["lineEdit5_text"]

    sql_sentence = f"INSERT INTO {table_name} (id,line_name,line_code,inspection_method,defects_parts," \
                   f"defects_level,inspection_date,defects_type,defects_description,img_count,source_image" \
                   f",img_path_1,img_path_2) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)"
    values = [rid, line_name, line_code, inspection_method, defects_parts, defects_level, inspection_date,
              defects_type, defects_description, img_count, source_image, img_path_1, img_path_2]

    return sql_sentence, values
