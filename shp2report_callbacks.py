import openpyxl_addin as oa
import os

######## callback functions here #############
def str_add(delim: str= '', **kargs):
    df = kargs.get('dataframe')
    idx = kargs.get('index')
    ret = []
    for field in kargs.get('fields'):
        datum = df.loc[idx, field]
        if not isinstance(datum, str):
            datum = str(datum)
        ret.append(datum)
    val = delim.join(ret)
    oa.set_data(sheet=kargs.get('sheet'), rng=kargs.get('rng'), data=val)

def str_deco(**kargs):
    prefix = kargs.get('prefix')
    postfix = kargs.get('postfix')
    field = kargs.get('fields')
    df = kargs.get('dataframe')
    idx = kargs.get('index')
    val = ''.join([prefix, df.loc[idx, field], postfix])
    oa.set_data(sheet=kargs.get('sheet'), rng=kargs.get('rng'), data=val)

def insert_image(**kargs):
    df = kargs.get('dataframe')
    idx = kargs.get('index')
    fields= kargs.get('fields')
    keep_ratio = kargs.get('keep_ratio', True)
    margin_px = kargs.get('margin_px', 4)

    if isinstance(fields, list):
        paths = []
        for field in fields:        
            datum = df.loc[idx, field]
            if not isinstance(datum, str):
                datum = str(datum)
            paths.append(datum)
        image_src = os.path.join(*paths)
    else:
        image_src = str(df.loc[idx, field])

    oa.insert_image(sheet=kargs.get('sheet'), rng=kargs.get('rng'), src=image_src, margin_px=margin_px, keep_ratio=keep_ratio)

