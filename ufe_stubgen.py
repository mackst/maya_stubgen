# -*- coding: utf-8 -*-

# 作者：石池

import os
import sys
import shutil
import subprocess

import ufe

def main():
    mayaBinDir = os.path.dirname(sys.executable)
    mayaPythonDir = os.path.abspath(os.path.join(mayaBinDir, '..', 'Python'))
    pyScriptsDir = os.path.join(mayaPythonDir, 'Scripts')
    # print(pyScriptsDir)
    # print(os.path.exists(pyScriptsDir))
    stubgenExe = os.path.join(pyScriptsDir, 'stubgen.exe')
    # print(stubgenExe)
    # print(os.path.exists(stubgenExe))

    ufeDir = os.path.dirname(ufe.__file__)
    try:
        _ufeDir = os.path.dirname(ufeDir)
        subprocess.check_call([stubgenExe, '-p', 'ufe.PyUfe', '-o', _ufeDir])
    except Exception as error:
        ufePyi = os.path.abspath('pyi/ufe')
        if os.path.exists(ufePyi):
            shutil.copytree(ufePyi, ufeDir, dirs_exist_ok=True)
            print('copy {} -> {}'.format(ufePyi, ufeDir))


# from html.parser import HTMLParser
# import inspect
# import keyword
# import typing
# import os

# import ufe



# class BaseMemItem(object):

#     def __init__(self) -> None:
#         self.name = ''
#         self.isStatic = False
#         self.doc = ''

# class MethoedMemItem(BaseMemItem):

#     def __init__(self) -> None:
#         super().__init__()
#         self.params = ''
    
#     def __str__(self) -> str:
#         d = {}
#         d[self.name] = (self.isStatic, self.doc, self.params)

#         return str(d)
    
#     __repr__ = __str__


# class UFEClassParaser(HTMLParser):

#     def __init__(self) -> None:
#         super().__init__()

#         self.detailedDescription = ''
#         self.memItems = {}
#         self.constructorItems = {}


# members = inspect.getmembers(ufe)
# for i in members:
#     print(i)
