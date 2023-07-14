

import os
from collections import namedtuple
import importlib
import pprint

import PySide2
from PySide2.support.generate_pyi import generate_all_pyi

def getModules() -> list[str]:
    modules = []
    for i in PySide2.__all__:
        try:
            importlib.import_module('PySide2.'+i)
            modules.append(i)
        except Exception as error:
            pass
    return modules

def genStubs(pyiOutDir: str = None):
    option = namedtuple('Options', ['modules', 'quiet', 'check', 'outpath', 'sys_path'])
    option.modules = getModules()
    option.quiet = False
    option.check = False
    option.outpath = pyiOutDir if pyiOutDir else os.path.dirname(PySide2.__file__)
    option.sys_path = []

    if pyiOutDir and not os.path.exists(pyiOutDir):
        os.makedirs(pyiOutDir)

    generate_all_pyi(option.outpath, option)


# pyiDir = os.path.join(os.path.dirname(__file__), 'pyi', 'PySide2')
# pyiDir = None
# genStubs(pyiDir)
