import yaml
import re, os, sys
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())
import LuaFilesParser

def find_yaml_value_by_key(data, key = '', valuelist = []):
    for k, v in data.items():
        if isinstance(v, dict):
            valuelist = find_yaml_value_by_key(v, key, valuelist)
        elif str(k) == key and str(v) != '':
            if str(v) not in valuelist:
                valuelist.append(str(v))
    return valuelist

def find_yaml_value_lua(data, flist=[]):
    for k, v in data.items():
        if isinstance(v, list) and all(isinstance(item, str) for item in v):
            pat = r'lua_(translator|processor|segmentor|filter)@(\*)?([^@]+)(@\w+)?'
            for it in v:
                mat = re.match(pat, it)
                if mat:
                    #print(mat.group(1), mat.group(2), mat.group(3), mat.group(4))
                    if mat.group(2) != None:
                        # replace . with /
                        fname = mat.group(3).replace('.', '/')
                        # for my librime-lua patch  
                        fname = fname.split('*')[0]
                        if fname not in flist:
                            flist.append(fname)
                    elif 'rime.lua' not in flist:
                        flist.append('rime.lua')
        elif isinstance(v, dict):
            find_yaml_value_lua(v, flist)
    return flist

"""
    from librime comments
    // Includes contents of nodes at specified paths.
    // __include: path/to/local/node
    // __include: filename[.yaml]:/path/to/external/node

    // Modifies subnodes or list elements at specified paths.
    // __patch: path/to/node
    // __patch: filename[.yaml]:/path/to/node
    // __patch: { key/alpha: value, key/beta: value }
"""
def get_external_files(fname, key='__include'):
    with open(fname, 'r', encoding=LuaFilesParser.encof(fname)) as f:
        data = yaml.load(f, yaml.FullLoader)
        f.close()
        pat = find_yaml_value_by_key(data, key = key, valuelist=[])
        res = []
        if len(pat) > 0:
            for p in pat:
                spl = p.split(':/')
                if len(spl) > 1:
                    if spl[0].endswith('.yaml') and (not (spl[0] in res)):
                        res.append(spl[0])
                    elif not ((spl[0]+'.yaml') in res):
                        res.append(spl[0]+'.yaml')
        return res

def get_import_preset_files(fname):
    with open(fname, 'r', encoding=LuaFilesParser.encof(fname)) as f:
        data = yaml.load(f, yaml.FullLoader)
        f.close()
        imports = find_yaml_value_by_key(data, 'import_preset', [])
        return [f'{it}.yaml' for it in imports if it not in ['default', 'symbos']]

def get_lua_files(fname, base_dir=''):
    with open(fname, 'r', encoding=LuaFilesParser.encof(fname)) as f:
        data = yaml.load(f, yaml.FullLoader)
        f.close()
        flist = find_yaml_value_lua(data, [])
        flist.append('rime')
        if base_dir == '':
            base_dir = os.path.dirname(fname)
        flist = LuaFilesParser.get_require_files(flist, base_dir)
        return [os.path.relpath(f, base_dir) for f in flist]
        #return flist

def get_dictionaries(fname):
    with open(fname, 'r', encoding=LuaFilesParser.encof(fname)) as f:
        data = yaml.load(f, yaml.FullLoader)
        f.close()
        return [f'{v}.dict.yaml' for v in find_yaml_value_by_key(data, 'dictionary')]

