import os

_data_dir = None
def data_dir():
    global _data_dir
    if _data_dir is None:
        paths = (['woger', 'data'], ['data'])
        for p in paths:
            apath = os.path.join(*p)
            if os.path.exists(apath):
                _data_dir = apath
                break



    return _data_dir

