@echo off
copy /y python38._pth .\python-3.8.10-embed-win32\
.\python-3.8.10-embed-win32\python.exe get-pip.py
.\python-3.8.10-embed-win32\Scripts\pip.exe install -r requirement.txt
