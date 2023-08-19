import pygit2
import os, sys, shutil
import argparse
from tqdm import tqdm
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())
import RppiParser

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
                print(f'{local_path} repo exists :) \n  now to update {local_path} repo')
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
            copied.append('{os.path.abspath(dest_file)}')
    return copied

def get_file_list_for_repo(repo_name=''):
    if repo_name =='':
        return []
    return []

# install a repo
def rppi_install_by_repo(repo = '', proxy='', mirror=default_mirror):
    set_proxy(proxy)
    if not rppi_update(mirror):
        print('update rppi failed')
        return
    rps = RppiParser.ParseIndex(f'{default_cache_dir}/rppi/index.json')
    recipes = RppiParser.FilterRecipe(rps, key='repo', value=repo)
    if len(recipes) == 0:
        print('find no recipes, now to exit')
        return
    repos = RppiParser.GetAllRecipesDependences(recipes[0])
    print(f"total find {len(recipes)} recipes, now to install {recipes[0]['name']} {recipes[0]['repo']}")
    for r in repos:
        local_path = r.split('/')[-1]
        local_path = f'{default_cache_dir}/{local_path}'
        if not clone_or_update_repo(mirror + '/' + r + '.git', local_path, False):
            print(f'clone {repo} failed')
            return
        conflicts = check_file_conflict(get_rime_user_dir(), local_path)
        if not not conflicts:
            print('conflicts:')
            for c in conflicts:
                print(c)
        else:
            print('no conflicts, now to copy files')
            dest = './' + get_rime_user_dir()
            src = local_path
            # todo: make exclude file list or include file list for repo
            # get_file_list_for_repo(local_path)
            copy_folder_contents(src, dest, ['.git', 'README.md', 'AUTHORS', 'LICENSE'])
    pass
# remove a repo
def rppi_remove_by_repo(repo = '', recursive=False, proxy='', mirror=default_mirror):
    set_proxy(proxy)
    rppi_update(mirror)
    rps = RppiParser.ParseIndex('./rppi/index.json')
    # todo: remove schema recipes
    pass
# clean cache
def rppi_clean_cache(cache_dir=default_cache_dir):
    pass
# list installed recipes
def rppi_list_installed():
    set_proxy(proxy)
    rppi_update(mirror)
    rps = RppiParser.ParseIndex('./rppi/index.json')
    # todo: list schema recipes installed
    pass

# test demos
if __name__ == '__main__':
    g_proxy = ''
    g_mirror = ''

    parser = argparse.ArgumentParser(description='sample')
    # add args 
    parser.add_argument('command', choices=['update', 'install', 'i' ,'search', 's', 'list', 'l'], help='command')
    parser.add_argument('value', nargs='?', help='target')

    parser.add_argument('-p', required=False, help="proxy url")
    parser.add_argument('-m', required=False, help="mirror url") 
    ###########################################################################
    # parse args
    args = parser.parse_args()
    ###########################################################################
    if args.p != None:
        g_proxy = args.p
        #print(f'proxy {g_proxy}')
    if args.m != None:
        g_mirror = args.m
        #print(f'mirror {g_mirror}')

    if args.command == 'update':
        rppi_update(mirror=g_mirror, proxy=g_proxy)
    elif args.command in ['install', 'i']:
        rppi_install_by_repo(args.value, proxy=g_proxy, mirror=g_mirror)
    elif args.command in ['search', 's']:
        rppi_search(value=args.value, proxy=g_proxy, mirror=g_mirror)
    elif args.command in ['list', 'l']:
        pass

