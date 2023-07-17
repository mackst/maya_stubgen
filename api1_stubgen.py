# -*- coding: utf-8 -*-

# 作者：石池


from html.parser import HTMLParser
import importlib
import inspect
import keyword
import io
import os
import re
import sys
import pprint
import typing

import docsConfig


def getClassLowerName(name: str) -> str:
    uppers = [c for c in name if c.isupper()]
    x = name
    for u in uppers:
        x = x.replace(u, '_'+u.lower())

    return x


class BaseMemItem(object):

    def __init__(self) -> None:
        self.name = ''
        self.isStatic = False
        self.doc = ''

class MethoedMemItem(BaseMemItem):

    def __init__(self) -> None:
        super().__init__()
        self.params = ''
    
    def __str__(self) -> str:
        d = {}
        d[self.name] = (self.isStatic, self.doc, self.params)

        return str(d)
    
    __repr__ = __str__


class Api1ClassParaser(HTMLParser):

    def __init__(self) -> None:
        super().__init__()

        self.detailedDescription = ''
        self.memItems = {}
        self.constructorItems = {}
        # self.dataItems = {}

        self.__memname = ''
        self.__memdoc = ''
        self.__memparams = ''
        self.__memitemStatic = False

        self.__ddStart = False
        self.__cddStart = False
        self.__mfdStart = False
        self.__mddStart = False

        self.__memitemStart = False
        self.__memnameStart = False
        self.__memdocStart = False
        self.__memparamsStart = False
        self.__memitemStaticStart = False

    def _pushConsItem(self):
        item = MethoedMemItem()
        item.name = self.__memname
        item.doc = self.__memdoc
        item.isStatic = self.__memitemStatic
        item.params = self.__memparams
        self.constructorItems[self.__memname.strip()] = item

        self.__memname = ''
        self.__memdoc = ''
        self.__memparams = ''
        self.__memitemStatic = False

    def _pushMemItem(self):
        item = MethoedMemItem()
        item.name = self.__memname
        item.doc = self.__memdoc
        item.isStatic = self.__memitemStatic
        item.params = self.__memparams
        self.memItems[self.__memname.strip()] = item

        self.__memname = ''
        self.__memdoc = ''
        self.__memparams = ''
        self.__memitemStatic = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, typing.Union[str, None]]]) -> None:
        if tag == 'div' and ('id', "dynsection-example0") in attrs:
            self.__ddStart = False
            return
        
        if tag == 'div' and ('class', 'memitem') in attrs and self.__cddStart:
            self.__memitemStart = True
            return
        
        if tag == 'div' and ('class', 'memitem') in attrs and self.__mfdStart:
            self.__memitemStart = True
            return
        
        if tag == 'table' and ('class', 'memname') in attrs and self.__memitemStart:
            self.__memnameStart = True
            return
        
        if tag == 'div' and ('class', 'memdoc') in attrs and self.__memitemStart:
            self.__memdocStart = True
            return
        
        if tag == 'table' and ('class', 'params') in attrs and self.__memitemStart:
            self.__memparamsStart = True
            return
        
        if tag == 'span' and ('class', 'mlabel') in attrs and self.__memitemStart:
            self.__memitemStaticStart = True

    def handle_endtag(self, tag: str) -> None:
        if tag == 'table' and self.__memnameStart:
            self.__memnameStart = False
            return
        
        if tag == 'div' and self.__memdocStart:
            self.__memitemStart = False
            self.__memnameStart = False
            self.__memdocStart = False
            self.__memparamsStart = False
            if self.__cddStart:
                self._pushConsItem()
            if self.__mfdStart:
                self._pushMemItem()
            return
        
        if tag == 'table' and self.__memparamsStart:
            self.__memparamsStart = False
            return

    def handle_data(self, data: str) -> None:
        if data == 'Detailed Description':
            self.__ddStart = True

        if data.endswith('Destructor Documentation'):
            self.__cddStart = True

        if data == 'Member Function Documentation':
            self.__cddStart = False
            self.__mfdStart = True

        if data == 'Member Data Documentation':
            self.__cddStart = False
            self.__mfdStart = False
            self.__mddStart = True

        # -------------------------------------------
        if self.__ddStart:
            self.detailedDescription += data

        if self.__memnameStart:
            self.__memname += data

        if self.__memdocStart:# and not self.__memparamsStart:
            self.__memdoc += data

        if self.__memparamsStart:
            self.__memparams += data

        if self.__memitemStaticStart:
            self.__memitemStatic = data.lower() == 'static'
            self.__memitemStaticStart = False


def getTypes(typeStr: str, className: str = '') -> str:
    builtinTypes = {
        '': str.__name__,
        'none': 'None',
        'void': 'None',
        'string': str.__name__,
        'char': str.__name__,
        'float': float.__name__,
        'double': float.__name__,
        'int': int.__name__,
        'short': int.__name__,
        'long': int.__name__,
        'bool': bool.__name__,
        'boolean': bool.__name__, 
        'true': bool.__name__,
        'false': bool.__name__,
        'bytearray': bytearray.__name__,
        'std.ostream': 'typing.TextIO'
    }
    
    typeStr = typeStr.replace('&', '')
    lower = typeStr.lower()
    if lower in builtinTypes:
        return builtinTypes[lower]
    
    if '::' in typeStr:
        return typeStr.replace('::', '.')
    
    return typeStr

def getParameterInfo(items: list[str]):
    pType = ''
    pName = ''
    count = len(items)
    if count == 2:
        pType = items[0].strip()
        pName = items[1].strip()
    elif count == 3:
        pType = items[1].strip()
        pName = items[2].strip()
    elif count == 4:
        pType = items[2].strip()
        pName = items[3].strip()

    if pName.count('[') > 0:
        pName = pName.split('[')[0]
        pType = 'list'

    if keyword.iskeyword(pName):
        pName += '_'

    pType = getTypes(pType)
    return (pName, pType)

def getConstructor(constructorItems: dict):
    NAMESPACE = 'OPENMAYA_MAJOR_NAMESPACE_OPEN'
    pyi = ''
    codeTemp = '    def __init__(self'
    for index, item in enumerate(constructorItems):
        sio = io.StringIO(item)
        name = ' '.join([i.strip() for i in sio.readlines() if i.strip()])
        # skip destructor
        if name.startswith('~'): continue

        itemData = constructorItems[item]
        code = ''
        if name.startswith(NAMESPACE):
            code = codeTemp + ', *args, **kws) -> None:\n'
            code += "\t\t''''''\n\n"
        else:
            code = codeTemp
            # Parameters
            paramStr = name.split('(')[1].split(')')[0].strip()
            if paramStr:
                parameters = paramStr.split(',')
                for para in parameters:
                    paraStr = para.strip()
                    if '=' in paraStr:
                        paraStr = paraStr.split('=')[0].strip()
                    
                    paraStr = paraStr.replace('&', '').replace('*', '')
                    pstrs = [i.strip() for i in paraStr.split(' ') if i.strip()]
                    pName, pType = getParameterInfo(pstrs)
                    code += ', {}: {} = ...'.format(pName, pType)
                code += ') -> None:\n'
                doc = itemData.doc.replace('\nParameters', '\n\n`Parameters:`').strip()
                doc = doc.replace('\n', '\n\t\t').expandtabs(4)
                code += "        '''{}\n        '''\n\n".format(doc)
            else:
                code = codeTemp + ', *args, **kws) -> None:\n'
                code += "\t\t''''''\n\n"

        if index != 0:
            code = '    @typing.overload\n' + code
        pyi += code.expandtabs(4)
    return pyi

def getFunctionNameInfo(signature: str):
    temp, paramStr = signature.split('(', 1)
    temp = temp.strip().replace('*', '').replace('&', '').replace('static', '')
    if '<' in temp:
        temp = temp.split('<')[0]
    temps = [i.strip() for i in temp.split(' ') if i.strip()]
    returnType = ''
    funcName = ''
    tempCount = len(temps)
    if tempCount == 2:
        returnType = temps[0]
        funcName = temps[1]
    elif tempCount == 3:
        returnType = temps[1]
        funcName = temps[2]

    returnType = getTypes(returnType)
    if paramStr.count(')') > 1:
        paramStr = ''
    else:
        paramStr = paramStr.split(')')[0].strip()
    return (funcName, paramStr, returnType)

def isOperator(item: str) -> bool:
    if not item.strip():
        return True
    
    out = False
    operators = (
        'operator',
        'operator()',
        'operator=',
        'operator<<',
        'operator!=',
        'operator+',
        'operator-',
        'operator bool',
    )
    out = any([i in item for i in operators])
    return out

def getFunctions(items: dict):
    ns = 'OPENMAYA_MAJOR_NAMESPACE_OPEN'
    pyi = ''
    codeTemp = '    def'
    staticCodeTemp = '\t@staticmethod\n'
    overload = '\t@typing.overload\n'

    funcNames = {}

    for item in items:
        if 'commonCreate' in item:
            pass
        # skip operator()
        if isOperator(item): continue

        code = codeTemp
        itemData = items[item]
        
        item = item.replace(ns, '').strip()
        sio = io.StringIO(item)
        name = ' '.join([i.strip() for i in sio.readlines() if i.strip()])

        # if '(' not in name:
        #     continue
        funcName, paramStr, returnType = getFunctionNameInfo(name)
        if keyword.iskeyword(funcName): continue
        if funcName in funcNames:
            code = overload + code

        if itemData.isStatic:
            code = staticCodeTemp + code + ' ' + funcName + '('
        else:
            code += ' ' + funcName + '(self'
        
        if paramStr:
            parameters = paramStr.split(',')
            for index, para in enumerate(parameters):
                paraStr = para.strip()
                if paraStr == 'void': continue
                if '=' in paraStr:
                    paraStr = paraStr.split('=')[0].strip()
                
                paraStr = paraStr.replace('&', '').replace('*', '')
                pstrs = [i.strip() for i in paraStr.split(' ') if i.strip()]
                pName, pType = getParameterInfo(pstrs)
                if itemData.isStatic and index == 0:
                    code += '{}: {} = ...'.format(pName, pType)
                else:
                    code += ', {}: {} = ...'.format(pName, pType)
            code += ') -> {}:\n'.format(returnType)
            doc = itemData.doc.replace('\nParameters', '\n\n`Parameters:`').strip()
            doc = doc.replace('\n', '\n\t\t')
            code += "        '''{}\n        '''\n\n".format(doc)
        else:
            if code.endswith('self'):
                code += ', '
            code += '*args, **kws) -> {}:\n'.format(returnType)
            code += "\t\t''''''\n\n"

        pyi += code.expandtabs(4)
        funcNames[funcName] = None

    return pyi



def getClassPYI(className: str, htmlDoc: str, class_: typing.Any):
    if className == 'MFnCamera':
        pass
    docString = "\t'''\n"
    docString += "\t{}\n"
    docStringEnd = "\t'''\n\n"
    baseClasses = inspect.getmro(class_)
    # bclsStr = ', '.join([cls.__name__ for cls in baseClasses[1:]])

    members = inspect.getmembers(class_)

    paraser = None
    with open(htmlDoc) as f:
        paraser = Api1ClassParaser()
        paraser.feed(f.read())

    clsPYI = 'class {}({}):\n\n'.format(className, baseClasses[1].__name__)

    # Constructors
    cstr = getConstructor(paraser.constructorItems)
    if not cstr:
        cstr = "    def __init__(self, *args, **kws) -> None:\n        ''''''\n\n"

    # memitems 
    funcs = getFunctions(paraser.memItems)

    # class attributes
    clsAttrStr = ''
    for member in members:
        memName = member[0]
        if memName.startswith('k') and memName[1].isupper():
            tn = type(member[1]).__name__
            x = '    {}: {} = ...\n'.format(memName, tn)
            clsAttrStr += x
    
    # doc string
    dstr = '\t' + paraser.detailedDescription.strip().replace('\n', '\n\t\t') + '\n\n'
    docString = docString.format(dstr)
    docString += docStringEnd
    clsPYI += docString.expandtabs(4)

    if clsAttrStr: clsAttrStr += '\n'
    clsPYI += clsAttrStr

    clsPYI += cstr
    clsPYI += funcs

    # print(clsPYI)
    return clsPYI

def emptyClass(name: str) -> str:
    clsPYI = 'class {}(object): ...\n\n'.format(name)
    return clsPYI

def writePYI(module: typing.Any, htmlTemp: str, pyiPath: str):
    # mFile = module.__file__
    members = inspect.getmembers(module)

    classStr = 'from __future__ import annotations\nimport typing\n\n'
    if module.__name__ != 'maya.OpenMaya':
        classStr += 'from maya.OpenMaya import *\n\n'

    moduleProperty = ''
    for member in members:
        name, mtype = member
        if inspect.isclass(mtype):
            # docName = 'class{}'.format(getClassLowerName(name))
            htmlDoc = htmlTemp.format(getClassLowerName(name))
            # 
            if not os.path.exists(htmlDoc):
                classStr += emptyClass(name)
                # print(f'{name} - {htmlDoc} : not exists')
                continue
            classStr += getClassPYI(name, htmlDoc, mtype)
            # break
        elif inspect.isfunction(mtype):
            # om_functions.append(i)
            pass
        elif inspect.isbuiltin(mtype):
            # om_builtins.append(i)
            pass
        else:
            # om_others.append(i)
            # print(name, type(mtype))
            isProperty = False
            if name.startswith('k'):
                if name[1].isupper():
                    isProperty = True

            if name.startswith('MAYA_'):
                isProperty = True
            if isProperty:
                moduleProperty += '\n{}: {} = ...\n'.format(name, type(mtype).__name__)
    
    classStr += '\n' + moduleProperty
    with open(pyiPath, 'w') as pyi:
        pyi.write(classStr)
    
def genAIPStubs(helpDir: str = '', pyiOutDir: str = None, modules: typing.Iterable = None):
    if not helpDir:
        return
    
    pyRefDir = os.path.join(helpDir, 'cpp_ref')
    if not os.path.exists(pyRefDir):
        return
    
    htmlTemp = os.path.join(pyRefDir, 'class{}.html')

    if not modules:
        modules = (
            'maya.OpenMaya',
            'maya.OpenMayaFX',
            'maya.OpenMayaUI',
            'maya.OpenMayaMPx',
            'maya.OpenMayaRender',
            'maya.OpenMayaAnim',
        )

    for m in modules:
        module = importlib.import_module(m)
        pyiPath, ext = os.path.splitext(os.path.abspath(module.__file__))
        if pyiOutDir:
            names = m.split('.')
            pyiPath = os.path.join(pyiOutDir, *names)
            if not os.path.exists(os.path.dirname(pyiPath)):
                os.makedirs(os.path.dirname(pyiPath))
        pyiPath += '.pyi'

        writePYI(module, htmlTemp, pyiPath)

        print('{} done.'.format(pyiPath))

def genFromStandalone():
    docDir = 'E:\\coding\\docs\\maya-2024-developer-help-enu'

    import maya.standalone as ms

    ms.initialize('python')

    # pyiDir = os.path.join(os.path.dirname(__file__), 'pyi')
    pyiDir = None
    genAIPStubs(docDir, pyiOutDir=pyiDir)

    ms.uninitialize()
    # sys.exit()

def onMayaDroppedPythonFile(obj):
    if os.path.exists(docsConfig.Paths.MAYA_API):
        genAIPStubs(docsConfig.Paths.MAYA_API, docsConfig.Paths.PYI_DIR)
