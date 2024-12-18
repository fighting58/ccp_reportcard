import openpyxl_addin as oa
import os
import numpy as np

######## callback functions here #############
def str_add(delim: str= '', **kargs):
    df = kargs.get('dataframe')
    idx = kargs.get('index')
    prefix = kargs.get('prefix', '')
    postfix = kargs.get('postfix', '')
    ret = []
    for field in kargs.get('fields'):
        datum = df.loc[idx, field]
        if not isinstance(datum, str):
            datum = str(datum)
        ret.append(datum)
    val = prefix + delim.join(ret) + postfix
    oa.set_data(sheet=kargs.get('sheet'), rng=kargs.get('rng'), data=val)

def str_deco(**kargs):
    prefix = kargs.get('prefix', '')
    postfix = kargs.get('postfix', '')
    field = kargs.get('fields')
    df = kargs.get('dataframe')
    idx = kargs.get('index')
    val = ''.join([prefix, df.loc[idx, field], postfix])
    oa.set_data(sheet=kargs.get('sheet'), rng=kargs.get('rng'), data=val)

def osa(**kargs):
    field = kargs.get('fields')
    df = kargs.get('dataframe')
    idx = kargs.get('index')
    val = f'{np.round(float(df.loc[idx, field]), 2):.2f}'
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

def hangul_date(**kargs):    
    df = kargs.get('dataframe')
    fields= kargs.get('fields')
    idx = kargs.get('index')
    datum = df.loc[idx, fields]

    data = datum.replace(' ', '')
    if '.' in data:    
        data = data.replace('.', '-') + '-'
        
    if '-' in data:
        year, month, day = data.split('-')[:3]
        data = ''.join([year,'년', f'{month:0>2}','월',f'{day:0>2}','일'])
    data = data.replace('년', '년 ').replace('월', '월 ')
    oa.set_data(sheet=kargs.get('sheet'), rng=kargs.get('rng'), data=data)

def toBL(**kargs):    
    df = kargs.get('dataframe')
    fields= kargs.get('fields')
    idx = kargs.get('index')
    datum = df.loc[idx, fields]

    if datum:
        datum = str(datum) 
        try: 
            temp = float(datum)
            datum = f'{datum.ljust(12, "0")}'
            idx = datum.index('.')
            d = datum[:idx]
            m = datum[idx+1:idx+3]
            s = datum[idx+3:idx+5]
            us = datum[idx+5:][:4]
            s = ".".join([s, us])
        except:
            datum= datum.replace(" ", "").replace('"', '').replace('˝', '')
            for c in "˚´°'":
                datum=datum.replace(c, "-")
            datum = f'{datum.ljust(12, "0")}'
            d, m, s = datum.split("-")
            s= f'{s[:7].ljust(7, "0")}'

        d=f'{d.rjust(4)}'
        data = "  ".join([d, m , s])
        oa.set_data(sheet=kargs.get('sheet'), rng=kargs.get('rng'), data=data)

