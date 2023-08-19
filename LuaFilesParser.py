from luaparser import ast
import codecs
import os

# check if utf-8 or utf-8-sig
def encof(fname):
    with open(fname, 'rb') as f:
        bom_check = f.read(4)
        if bom_check[:3] == codecs.BOM_UTF8:
            return 'utf-8-sig'
        else:
            return 'utf-8'

# collect_requires by require and dofile
def collect_requires(tree, requires = []):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and (node.func.id == 'require' or node.func.id == 'dofile'):
            if len(node.args) > 0 and isinstance(node.args[0], ast.String):
                if node.args[0].s not in requires:
                    requires.append(node.args[0].s)
    return requires

# possible_file path for librime-lua
def possible_file(module, base_dir = '.'):
    return [
            os.path.abspath(base_dir + '/' + module + '.lua'),
            os.path.abspath(base_dir + '/lua/' + module + '.lua'),
            os.path.abspath(base_dir + '/lua/' + module + '/init.lua')
            ]

# get required files list
def get_require_files(base_file, base_dir = './'):
    if base_dir == '.':
        base_dir = './'

    tree = ast.parse(open(base_dir + base_file, 'r', encoding=encof(base_dir + base_file)).read())
    requires = collect_requires(tree, [])
    freq = []
    for r in requires:
        fp = possible_file(r, base_dir)
        for f in fp:
            if os.path.exists(f):
                tree = ast.parse(open(f, 'r', encoding=encof(f)).read())
                requires = collect_requires(tree, requires)
                freq.append(os.path.abspath(f))
    return freq

# possible_files file name without path
def get_require_files(possible_files=[], base_dir='./'):
    if len(possible_files) > 0:
        requires = []
        res = []
        for l in possible_files:
            pfs = possible_file(l, base_dir)
            for pf in pfs:
                if os.path.exists(pf):
                    tree = ast.parse(open(pf, 'r', encoding=encof(pf)).read())
                    requires = collect_requires(tree, requires)
                    res.append(os.path.abspath(pf))
        return res
