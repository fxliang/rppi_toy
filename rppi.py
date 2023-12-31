import pygit2
import os, sys, shutil
import argparse
from tqdm import tqdm
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())
import RppiParser
import json

if sys.platform == "win32": # Windows
    import winreg
    # get registry string value 
    def get_registry_string_value(key, subkey, value_name):
        try:
            reg_key = winreg.OpenKey(key, subkey)
            value, _ = winreg.QueryValueEx(reg_key, value_name)
            winreg.CloseKey(reg_key)
            return value
        except WindowsError:
            return None

    # get weasel user dir
    def get_rime_user_dir():
        key = winreg.HKEY_CURRENT_USER
        subkey = r'SOFTWARE\Rime\Weasel'
        value_name = 'RimeUserDir'
        user_dir = get_registry_string_value(key, subkey, value_name)
        # by now, for testing, return usr, if you want to really use it, change
        # to return user_dir
        return 'usr'
        #return user_dir
else:
    pass

default_mirror = 'https://github.com'
default_cache_dir = './cache'

# set up proxy
def set_proxy(proxy):
    os.environ['http_proxy'] = proxy
    os.environ['https_proxy'] = proxy

# callbacks for clone process
class CloneRemoteCallbacks(pygit2.RemoteCallbacks):
    def __init__(self):
        self.pbar = tqdm(total=100, unit=' objects', colour='green', leave=True)
        self.proc = 0
    def transfer_progress(self, stats):
        self.pbar.total = stats.total_objects
        tmp = stats.indexed_objects - self.proc
        self.proc = stats.indexed_objects
        if stats.total_objects > 0:
            self.pbar.update(tmp)

# test a path is a repo or not
def test_repo(path):
    try:
        return pygit2.Repository(path)
    except:
        return None

# clone or update a repo
def clone_or_update_repo(url, local_path, silent=True):
    try:
        repo = test_repo(local_path)
        if repo != None:
            if not silent:
                print('------------------------------------------------------')
                print(f'{local_path} repo exists :) \n  update {local_path} repo now')
            remote = repo.remotes['origin']
            remote.fetch()
            main_branch = ['master' , 'main']
            mb_name = main_branch[0]
            try:
                lb = repo.branches[main_branch[0]]
                rb = repo.branches['origin/' + main_branch[0]]
            except:
                lb = repo.branches[main_branch[1]]
                rb = repo.branches['origin/' + main_branch[1]]
                mb_name = main_branch[1]

            lb.set_target(rb.target)
            repo.checkout(lb)
            if not silent:
                print('  branch ' + mb_name +' is up to date')
            pass
        else:
            if not silent:
                print(f'Clone {url} into {local_path}')
            pygit2.clone_repository(url, local_path, callbacks=CloneRemoteCallbacks())
        return True
    except pygit2.errors.GitError as e:
        print("error as", str(e))
        return False

# update rppi index
def rppi_update(mirror = default_mirror, proxy='', silent=False):
    set_proxy(proxy)
    url = mirror + '/rime/rppi.git'
    return clone_or_update_repo(url, f'{default_cache_dir}/rppi', silent = silent)

# search key_word in rppi index
def rppi_search(key='', value='', proxy='', mirror=''):
    set_proxy(proxy)
    repo = test_repo(f'{default_cache_dir}/rppi')
    if repo == None:
        rppi_update(mirror = mirror, proxy=proxy)
    fr = RppiParser.ParseIndex(f'{default_cache_dir}/rppi/index.json')
    if value != None:
        fr = RppiParser.FilterRecipe(fr, key=key, value=value)
    for r in fr:
        print(r['categories'], r['name'], f"\t{r['repo']}")

    return fr

# get files name
def get_all_files(directory):
    """递归获取目录及其子目录中的所有文件名"""
    file_set = set()
    for root, dirs, files in os.walk(directory):
        for file in files:
            #file_set.add(os.path.join(root, file))
            file_set.add(file)
    return file_set
# for installing file checking
def check_file_conflict(src, dst):
    """递归检查源目录和目标目录中的文件冲突"""
    # 获取源目录和目标目录下的所有文件名
    src_files = get_all_files(src)
    dst_files = get_all_files(dst)
    # 检查文件名冲突
    filename_conflict = src_files & dst_files
    return filename_conflict
# copy files from src folder to dest folder, exclude files/folder in exclude
def copy_folder_contents(source_folder, destination_folder, exclude_list=[]):
    # 遍历源文件夹中的所有文件和文件夹
    copied = []
    for root, dirs, files in os.walk(source_folder):
        # 排除清单内的文件夹和文件
        dirs[:] = [d for d in dirs if d not in exclude_list]
        files[:] = [f for f in files if f not in exclude_list]
        # 构建目标文件夹路径
        dest_root = root.replace(source_folder, destination_folder)
        # 创建目标文件夹
        os.makedirs(dest_root, exist_ok=True)
        # 复制文件
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_root, file)
            shutil.copy2(src_file, dest_file)
            print(f'copied file: {os.path.abspath(dest_file)}')
            copied.append(f'{os.path.abspath(dest_file)}')
    return copied

# copy files from src folder to dest folder, exclude files/folder in exclude
def get_installed_recipe_files(source_folder, destination_folder, exclude_list=[]):
    # 遍历源文件夹中的所有文件和文件夹
    installed = []
    for root, dirs, files in os.walk(source_folder):
        # 排除清单内的文件夹和文件
        dirs[:] = [d for d in dirs if d not in exclude_list]
        files[:] = [f for f in files if f not in exclude_list]
        # 构建目标文件夹路径
        dest_root = root.replace(source_folder, destination_folder)
        # 创建目标文件夹
        os.makedirs(dest_root, exist_ok=True)
        # 复制文件
        for file in files:
            dest_file = os.path.join(dest_root, file)
            installed.append(f'{os.path.abspath(dest_file)}')
    return installed

def get_file_list_for_repo(repo_name=''):
    if repo_name =='':
        return []
    return []

def rppi_remove_by_repo(repo='', auto = False, proxy='', mirror = default_mirror):
    set_proxy(proxy)
    if not rppi_update(mirror):
        print('update rppi failed')
        return
    rps = RppiParser.ParseIndex(f'{default_cache_dir}/rppi/index.json')
    recipes = RppiParser.FilterRecipe(rps, key='repo', value=repo)
    if len(recipes) > 1:
        print('find more than 1 recipes, please ensure the recipe name, exit now')
        for r in recipes:
            print(r['name'], r['repo'])
        return
    repos = RppiParser.GetAllRecipesDependences(recipes[0])
    if auto:
        print('remove follow installed recipes')
        for r in repos:
            print(r)
    for r in repos:
        local_path = r.split('/')[-1]
        local_path = f'{default_cache_dir}/{local_path}'
        if not clone_or_update_repo(mirror + '/' + r + '.git', local_path, False):
            print(f'clone or upgrade {repo} failed')
            return
        record_remove_repo(r)
        dest = get_rime_user_dir()
        src = local_path
        files_to_del = get_installed_recipe_files(src, dest, ['.git', 'README.md', 'AUTHORS', 'LICENSE'])
        for file in files_to_del:
            try:
                os.remove(file)
            except:
                pass
            print(f'remove file: {file}')
        if not auto:
            break
    pass

# install a repo
def rppi_install_by_repo(repo = '', upgrade = False, proxy='', mirror=default_mirror):
    set_proxy(proxy)
    if not rppi_update(mirror):
        print('update rppi failed')
        return
    rps = RppiParser.ParseIndex(f'{default_cache_dir}/rppi/index.json')
    recipes = RppiParser.FilterRecipe(rps, key='repo', value=repo)
    if len(recipes) == 0:
        print('find no recipes, exit now')
        return
    repos = RppiParser.GetAllRecipesDependences(recipes[0])
    if upgrade:
        action = 'upgrade'
    else:
        action = 'install'
    print(f"total find {len(recipes)} recipes, {action} {recipes[0]['name']} {recipes[0]['repo']} now")
    for r in repos:
        local_path = r.split('/')[-1]
        local_path = f'{default_cache_dir}/{local_path}'
        if not clone_or_update_repo(mirror + '/' + r + '.git', local_path, False):
            print(f'clone or upgrade {repo} failed')
            return
        record_installed_repo(r)
        conflicts = check_file_conflict(get_rime_user_dir(), local_path)
        if not not conflicts and not upgrade:
            print('conflicts:')
            for c in conflicts:
                print(c)
        else:
            if upgrade:
                print('upgrade files now')
            else:
                print('no conflicts, copy files now')
            dest = get_rime_user_dir()
            src = local_path
            # todo: make exclude file list or include file list for repo
            # get_file_list_for_repo(local_path)
            copy_folder_contents(src, dest, ['.git', 'README.md', 'AUTHORS', 'LICENSE'])
    pass

def record_installed_repo(repo):
    if not os.path.exists('installed.json'):
        init_data = { 'installed': [repo] }
        with open('installed.json', 'w') as f:
            json.dump(init_data, f, indent=2)
    else:
        with open('installed.json') as f:
            data = json.load(f)
        if repo not in data['installed']:
            data['installed'].append(repo)
        with open('installed.json', 'w') as f:
            json.dump(data, f, indent=2)

def record_remove_repo(repo):
    if not os.path.exists('installed.json'):
        init_data = { 'installed': [] }
        with open('installed.json', 'w') as f:
            json.dump(init_data, f, indent=2)
    else:
        with open('installed.json') as f:
            data = json.load(f)
        if repo in data['installed']:
            data['installed'].remove(repo)
        with open('installed.json', 'w') as f:
            json.dump(data, f, indent=2)

# clean cache
def rppi_clean_cache(cache_dir=default_cache_dir):
    pass

# list installed, available, all recipes
def rppi_list(param, proxy='', mirror=default_mirror):
    set_proxy(proxy)
    rppi_update(mirror = mirror, proxy=proxy)
    fr = RppiParser.ParseIndex(f'{default_cache_dir}/rppi/index.json')
    if param == 'all' or param==None:
        for r in fr:
            print(r['categories'], r['name'], f"\t{r['repo']}")
    else:
        with open('installed.json') as f:
            data = json.load(f)
        installed_repoes = data['installed']
        if param=='installed':
            for repo in installed_repoes:
                for r in fr:
                    if r['repo'] == repo:
                        print(r['categories'], r['name'], f"\t{r['repo']}")
        elif param=='available':
            for r in fr:
                if r['repo'] not in installed_repoes:
                    print(r['categories'], r['name'], f"\t{r['repo']}")

import configparser
# test demos
if __name__ == '__main__':
    g_proxy = ''
    g_mirror = ''

    config = configparser.ConfigParser()
    config.read('rppi.conf')
    try:
        proxy_conf = config.get('config', 'http_proxy')
    except:
        proxy_conf = None
    try:
        mirror_conf = config.get('config', 'mirror')
    except:
        mirror_conf = None

    parser = argparse.ArgumentParser(description='sample')
    # add args 
    parser.add_argument('command', choices=['update', 'install', 'i' ,'search', 's', 'list', 'l', 'upgrade', 'u', 'remove', 'purge'], help='command')
    parser.add_argument('value', nargs='?', help='target')

    parser.add_argument('-p', required=False, help="proxy url")
    parser.add_argument('-m', required=False, help="mirror url") 
    ###########################################################################
    # parse args
    args = parser.parse_args()
    ###########################################################################

    if args.p != None:
        g_proxy = args.p
    elif proxy_conf != None:
        g_proxy = proxy_conf

    if args.m != None:
        g_mirror = args.m
    elif mirror_conf != None:
        g_mirror = mirror_conf
    else:
        g_mirror = default_mirror

    # update rppi index
    if args.command == 'update':
        rppi_update(mirror=g_mirror, proxy=g_proxy)
    # install recipe by key word or repo name
    elif args.command in ['install', 'i']:
        rppi_install_by_repo(args.value, proxy=g_proxy, mirror=g_mirror)
    # remove repo only
    elif args.command == 'remove':
        rppi_remove_by_repo(args.value, proxy=g_proxy, mirror=g_mirror)
    # remove repo and it's dependencies
    elif args.command == 'purge':
        rppi_remove_by_repo(args.value, auto=True, proxy=g_proxy, mirror=g_mirror)
    # upgrade recipe by key word or repo name
    elif args.command in ['upgrade', 'u']:
        rppi_install_by_repo(args.value, upgrade = True, proxy=g_proxy, mirror=g_mirror)
    # search repo info by key word
    elif args.command in ['search', 's']:
        rppi_search(value=args.value, proxy=g_proxy, mirror=g_mirror)
    # todo: list info
    elif args.command in ['list', 'l']:
        rppi_list(args.value, proxy=g_proxy, mirror = g_mirror)
        pass

