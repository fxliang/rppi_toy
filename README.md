A demo toy to play with rime/rppi

currently, cache rppi index and recipes in `/path/to/this/toy/cache`, install recipes in `/path/to/this/toy/usr`

if you want to install recipes in your weasel user directory, modify rppi.py line 26 to line 30 like bellow

```python
        user_dir = get_registry_string_value(key, subkey, value_name)
        # by now, for testing, return usr, if you want to really use it, change
        # to return user_dir
        #return 'usr'
        return user_dir

```

require packages:

```
tqdm
pyyaml
luaparser
pygit2
argparse
```

pip to get packages, with

[get-pip.py](!https://bootstrap.pypa.io/get-pip.py)

------------------------------------------------------

to make it portable on windows, use python embed distro

[python-3.8.10-embed on huaweicloud.com](!https://mirrors.huaweicloud.com/python/3.8.10/python-3.8.10-embed-win32.zip)

to use pip with python embed, modify `python38._pth` as follow

```python
python38.zip
.

# Uncomment to run site.main() automatically
import site

```
install pip for python embed with command bellow

```
[path/to/pythom-embed/python.exe] /path/to/get-pip.py
```

install packages with command bellow

```
[path/to/pip/in/python-embed/Script/]pip.exe install tqdm pyyaml luaparser pygit2 argparse 
```

modify rppi.bat if your path is not the same as mine

to use it with proxy, command with -p http_proxy_url like bellow

```
rppi -p http://localhost:8118 other_command
```

to use it with github mirror(esp for network limitation situation), command with -m github_mirror_url, like bellow

```
rppi -m http://hub.njuu.cf other_command
```

to install recipe in rppi, use 
```
rppi i recipe_name
```

to search 

```
rppi s key_word
```

to update rppi index

```
rppi update
```

to upgrade a repo
```
rppi.bat upgrade repo_name_or_keyword
```