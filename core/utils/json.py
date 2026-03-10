import json


def dict_level1_to_str(body: dict):
    new_body = {}
    for key, value in body:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        new_body[key] = value
    return new_body
