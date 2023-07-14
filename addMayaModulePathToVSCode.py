
import json
import os

import maya.standalone as ms

ms.initialize('python')
maya.cmds.loadPlugin('mayaUsdPlugin')

import pxr

Force = False

vscodeDir = os.path.abspath('.vscode')
settings = os.path.join(vscodeDir, 'settings.json')

if Force:
    if not os.path.exists(vscodeDir):
        os.mkdir(vscodeDir)
    
s = {}
if os.path.exists(settings):
    with open(settings, encoding='utf8') as f:
        content = f.read()
        if content:
            s = json.loads(content)

ep = 'python.autoComplete.extraPaths'
ep_a = 'python.analysis.extraPaths'
py = 'python.defaultInterpreterPath'

epaths = s.get(ep, [])

pxrDir = os.path.dirname(os.path.dirname(pxr.__file__))
if pxrDir not in epaths: epaths.append(pxrDir)
mayaUsdDir = os.path.abspath(os.path.join(pxrDir, '..', '..', '..'))
mayaUsdLib = os.path.join(mayaUsdDir, 'MayaUSD', 'lib', 'python')
if mayaUsdLib not in epaths: epaths.append(mayaUsdLib)
s[ep] = epaths
s[ep_a] = epaths

# set mayapy as defaultInterpreterPath
# mayaMDir = os.path.dirname(ms.__file__)
# mayaDir = os.path.abspath(os.path.join(mayaMDir, '..', '..', '..', '..'))
# mayapy = os.path.join(mayaDir, 'bin', 'mayapy.exe')
# s[py] = mayapy

with open(settings, 'w') as f:
    json.dump(s, f, indent=4)
