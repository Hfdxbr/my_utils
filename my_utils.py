import json

import pandas


class ddict(dict):
    def __init__(self, *args, **kwargs):
        super(ddict, self).__init__(*args, **kwargs)

    def __getitem__(self, key_list):
        if not isinstance(key_list, list):
            key_list = [key_list]
        dict_list = [super(ddict, self)]
        for key in key_list[:len(key_list) - 1]:
            dict_list[-1].setdefault(key, {})
            dict_list.append(dict_list[-1].__getitem__(key))
        return dict_list[-1].__getitem__(key_list[-1])

    def __setitem__(self, key_list, value):
        if not isinstance(key_list, list):
            key_list = [key_list]
        dict_list = [super(ddict, self)]
        for key in key_list[:len(key_list) - 1]:
            dict_list[-1].setdefault(key, {})
            dict_list.append(dict_list[-1].__getitem__(key))
        dict_list[-1].__setitem__(key_list[-1], value)


def df_to_ddict(df: pandas.DataFrame, index):
    if not isinstance(index, list):
        index = [index]
    mindex = pandas.MultiIndex.from_frame(df[index])
    df.index = mindex
    df = df.drop(columns=index)
    d = ddict()
    for k, v in df.to_dict('index').items():
        d[list(k)] = v
    return d


def df_to_json(df: pandas.DataFrame, index, file=None, **kwargs):
    d = df_to_ddict(df, index)
    if file is None:
        return json.dumps(d, **kwargs)
    else:
        with open(file, 'w') as f:
            json.dump(d, f, **kwargs)
