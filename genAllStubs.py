# -*- coding: utf-8 -*-

# 作者：石池


from importlib import reload
import os

import cmds_stubgen
import api1_stubgen
import api20_stubgen
import ufe_stubgen
import usd_stubgen
import pyside_stubgen
import docsConfig


# docsConfig.Paths.PYI_DIR = os.path.join(os.path.dirname(__file__), 'pyi')

def main():
    cmds_stubgen.genCmdStubs(docsConfig.Paths.MAYA_HELP, docsConfig.Paths.PYI_DIR)
    api1_stubgen.genAIPStubs(docsConfig.Paths.MAYA_API, docsConfig.Paths.PYI_DIR)
    api20_stubgen.genAIP20Stubs(docsConfig.Paths.MAYA_API, docsConfig.Paths.PYI_DIR)
    ufe_stubgen.main()
    usd_stubgen.genUsdStubs(docsConfig.Paths.USD_XML, docsConfig.Paths.PYI_DIR)
    pyside_stubgen.genStubs(docsConfig.Paths.PYI_DIR)
    print('done')

def onMayaDroppedPythonFile(obj):
    # reload(cmds_stubgen)
    # reload(api1_stubgen)
    # reload(api20_stubgen)
    # reload(usd_stubgen)
    # reload(docsConfig)
    main()

