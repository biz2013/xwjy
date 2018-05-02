
import os, jinja2, hashlib


def jinja2_render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')
    ).get_template(filename).render(context)


def sign_test_json(json, key):
    sorted_keys = sorted(json.keys())
    str_to_be_signed = ""
    for key in sorted_keys:
        str_to_be_signed = '{0}{1}={2}&'.format(str_to_be_signed, key, json[key])
    str_to_be_signed = '{0}key={1}'.format(str_to_be_signed, key)
    m = hashlib.md5()
    m.update(str_to_be_signed.encode('utf-8'))
    return m.hexdigest().upper()
