# -*- coding: utf-8 -*-

# 作者：石池

import os
import re
import sys
import importlib
import inspect
import keyword
import builtins
import typing
import xml.etree.ElementTree as et

import docsConfig


def getClassLowerName(name: str) -> str:
    uppers = [c for c in name if c.isupper()]
    x = name
    for u in uppers:
        x = x.replace(u, '_'+u.lower())

    return x

def getXmlName(moduleName: str, className: str) -> str:
    m = getClassLowerName(moduleName)
    c = getClassLowerName(className)

    return m+c

def getUSDTypeName(name: str) -> str:
    typeNames = ('Handle', 'RefPtr')
    for n in typeNames:
        if name.strip().endswith(n):
            name = name.replace(n, '')

    name = name.replace('::', '.').strip()
    moduleName = ''
    for i in pxr.__all__:
        # found = False
        if name.startswith(i):
            moduleName = i
            break
        #     tName = name.replace(i, '')
        #     try:
        #         exec('from pxr.{} import {}'.format(i, tName))
        #         moduleName = i
        #         found = True
        #     except Exception:
        #         for x in pxr.__all__:
        #             try:
        #                 exec('from pxr.{} import {}'.format(i, tName))
        #                 moduleName = x
        #                 found = True
        #                 break
        #             except Exception:
        #                 pass
        # if found:
        #     break
    
    # fullTypeName = 'pxr.{}.{}'.format(moduleName, name.replace(moduleName, ''))
    if '<' in name and '>' in name:
        typeName, itemName = name.split('<')
        itemName = itemName.split('>')[0].strip()
        itemType = getUSDTypeName(itemName)
        typeName = 'pxr.{}.{}'.format(moduleName, typeName.replace(moduleName, '').strip())
        return '{}[{}]'.format(typeName, itemType)
    
    if moduleName:
        return 'pxr.{}.{}'.format(moduleName, name.replace(moduleName, ''))

    return name

# usd_classes = {}
# usd_funcs = []
# usd_builtins = []
# members = inspect.getmembers(pxr.Usd)
# for i in members:
#     if inspect.isclass(i[1]):
#         usd_classes[i[0]] = i[1]
#     elif inspect.isfunction(i[1]):
#         usd_funcs.append(i[0])
#     elif inspect.isbuiltin(i[1]):
#         usd_builtins.append(i[0])


# print(usd_classes)
# print('-'*150)
# print(usd_funcs)
# print('-'*150)
# print(usd_builtins)

# print(usd_classes['Attribute'].__class__)

# xmlDocDir = 'E:\\coding\\libs\\usd_build\\docs\\doxy_xml'
# for clsName in usd_classes:
#     xmlName = 'class' + getXmlName('Usd', clsName) + '.xml'
#     xmlPath = os.path.join(xmlDocDir, xmlName)
    # if not os.path.exists(xmlPath):
    #     print(clsName, usd_classes[clsName])

# import stubgen
# stubgen.genUSD(['pxr.{}._{}'.format(i, i[0].lower()+i[1:]) for i in pxr.__all__])
# import pprint

# pprint.pprint(['pxr.'+i for i in pxr.__all__])



# ms.uninitialize()
# sys.exit()



BuiltinTypes = {
    '': 'None',
    'none': 'None',
    'void': 'None',
    'string': str.__name__,
    'std::string': str.__name__,
    'char': str.__name__,
    'float': float.__name__,
    'double': float.__name__,
    'int': int.__name__,
    'short': int.__name__,
    'size_t': int.__name__,
    'long': int.__name__,
    'int64_t': int.__name__,
    'bool': bool.__name__,
    'boolean': bool.__name__, 
    'true': bool.__name__,
    'false': bool.__name__,
    'bytearray': bytearray.__name__,
    'std::ostream': 'typing.TextIO',
    'file': 'typing.TextIO',
    'std::type_info': 'typing.Any',
    'std::pair': 'dict',
    'mapping': 'dict',
    'fileformatarguments': 'dict',
    '_iterator': 'typing.Iterator',
    'iterator': 'typing.Iterator',

    # '_node': 'typing.Any',
    # 'calltree': 'typing.Any',
    # 'filter': 'typing.Any',
    # 'weakprobeptr': 'typing.Any',
    # 'weakprobeptr': 'typing.Any',
    # 'lptr': 'typing.Any',
    # 'senderptr': 'typing.Any',
    # 'methodptr': 'typing.Callable',
    # 'propertypredicatefunc': 'typing.Any',
    # 'tokentotokenvectormap': 'typing.Any',
    # 'computeinterpolationinfo': 'typing.Any',
    # 'purposeinfo': 'typing.Any',
    # 'protoxforminclusion': 'typing.Any',
}


def getReturnType(tStr: str):
    if tStr is None:
        ts = ('None', None)
        return ts
    apiNames = (
        'constexpr', 'unsigned'
    )
    ts = tStr
    apiNS = '_API'
    if apiNS in ts:
        ts = ts.split(apiNS)[1].strip()
    else:
        for i in apiNames:
            ts = ts.replace(i, '').strip()
    return getTypeNameFromCPPType(ts)

def getTypeNameFromCPPType(tStr: str, moduleName: str = '') -> tuple[str, str | None]:
    ts = tStr.replace('*', '').strip()
    ts = ts.replace('&', '').strip()
    ts = ts.replace('const', '').strip()
    ts = ts.replace('class ', '').strip()
    ts = ts.replace('...', '').strip()
    tlower = ts.lower()
    if tlower in BuiltinTypes:
        return (BuiltinTypes[tlower], None)
    if tlower == 't':
        return ('typing.Any', None)
    
    if tlower.startswith('boost::python'):
        return (tStr.split('::')[-1], None)
    
    # vector
    if tlower.startswith('std::vector<') or tlower.startswith('std::set<'):
        v = 'list[{}]'
        vt = ts.split('<')[1].split('>')[0].strip()
        vts = getTypeNameFromCPPType(vt)
        return (v.format(vts[0]), None)
    
    # dict
    if tlower.startswith('std::pair<'):
        d = 'dict[{}, {}]'
        dt = ts.split('<')[1].split('>')[0].strip()
        dts = dt.split(',')
        dt1 = getTypeNameFromCPPType(dts[0].strip())
        dt2 = getTypeNameFromCPPType(dts[1].strip())
        # TODO import module?
        return (d.format(dt1[0], dt2[0]), None)
    
    # function callback
    if tlower.startswith('std::function'):
        return ('typing.Callable', None)
    
    # shared_ptr unique_ptr
    if tlower.startswith('std::shared_ptr<') or tlower.startswith('std::unique_ptr<'):
        sp = ts.split('<')[1].split('>')[0].strip()
        return getTypeNameFromCPPType(sp)
    
    if ts[0].isupper():
        usdType = getUSDTypeName(ts)
        if '.' in usdType:
            im = usdType
            if '[' in usdType:
                im = usdType.split('[')[0]
            im = im.split('.')
            im = '{}.{}'.format(im[0], im[1])
            return (usdType, im)
    return (ts, None)

def getParentClassName(className: str, cls: typing.Any) -> str:
    pclasses = {
        'instance': 'object'
    }
    m = cls.__qualname__
    module = inspect.getmodule(cls)
    if module:
        fullClsName = module.__name__ + '.' + pclasses.get(className, className)
        return fullClsName
    return pclasses.get(className, className)
    return fullClsName

def getOperatorFunc(funcName: str) -> str:
    codeTemp = '    def __{}__(self{}) -> {}: ...\n\n'
    operators = {
        'operator bool': codeTemp.format('bool', '', 'bool'),
        'operator!': codeTemp.format('bool', '', 'bool'),
        'operator==': codeTemp.format('eq', ', other', 'bool'),
        'operator<': codeTemp.format('lt', ', other', 'bool'),
        'operator>': codeTemp.format('gt', ', other', 'bool'),
        'operator!=': codeTemp.format('ne', ', other', 'bool'),
        'operator<=': codeTemp.format('le', ', other', 'bool'),
        'operator>=': codeTemp.format('ge', ', other', 'bool'),

        'operator[]': codeTemp.format('getitem', '', 'typing.Any'),
        'operator-': codeTemp.format('neg', '', 'typing.Any'),
        'operator+': codeTemp.format('pos', '', 'typing.Any'),

        'operator+=': codeTemp.format('iadd', ', other', 'typing.Any'),
        'operator-=': codeTemp.format('isub', ', other', 'typing.Any'),
        'operator*=': codeTemp.format('imul', ', other', 'typing.Any'),
        'operator/=': codeTemp.format('itruediv', ', other', 'typing.Any'),
        'operator&=': codeTemp.format('iand', ', other', 'typing.Any'),
        'operator|=': codeTemp.format('ior', ', other', 'typing.Any'),

        'operator*': codeTemp.format('mul', ', other', 'typing.Any'),
        'operator/': codeTemp.format('truediv', ', other', 'typing.Any'),
        'operator<<': codeTemp.format('lshift', ', other', 'typing.Any'),
        'operator>>': codeTemp.format('rshift', ', other', 'typing.Any'),
        'operator&': codeTemp.format('and', ', other', 'typing.Any'),
        'operator|': codeTemp.format('or', ', other', 'typing.Any'),

        'operator T': '',
        'operator UnspecifiedBoolType': '',
        'operator=': '',
    }
    funcStr = codeTemp.format(funcName, '', 'None')
    if len(funcName) > len('operator bool '):
        funcStr = ''
    return operators.get(funcName, funcStr)

def getClassEnumFromXml(memdef: et.Element) -> str:
    names = {}
    out = ''
    for i in memdef.findall('enumvalue'):
        name = i.find('name').text
        out += '    {}: typing.ClassVar[int] = ...\n'.format(name)
        names[name] = None
    return (out, names)

def getClassPyiFromXml(className: str, xmlDoc: str, parentClass: str = '', moduleName: str='') -> str:
    funcNames = {}
    enumNames = {}
    importModules = {}
    tree = et.parse(xmlDoc)
    root = tree.getroot()
    code = 'class {}({}):\n\n'.format(className, parentClass)
    enumCode = ''
    variableCode = ''
    if className == "ResolverContext":
        pass
    for memdef in root.iter('memberdef'):
        # print(memdef.attrib)
        kind = memdef.attrib['kind']  # function / enum
        prot = memdef.attrib['prot']
        isStatic = memdef.attrib['static'] == 'yes'
        isPublic = prot == 'public'
        # if kind == 'function' and isPublic:
        if kind in ('function', 'friend') and isPublic:
            returnType = ''
            rt = memdef.find('type')
            rtRef = rt.find('ref')
            if rtRef is None:
                returnType = rt.text
            else:
                returnType = rtRef.text
            funcName = memdef.find('name').text
            if funcName.startswith('~'): continue
            if funcName.startswith('operator'):
                code += getOperatorFunc(funcName)
                continue
            
            isInitFunc = funcName.endswith(className) and funcName[0].isupper()
            if funcName == className or isInitFunc:
                funcName = '__init__'

            if funcName == 'IsAuthoredAt':
                pass
            detaileddescription = ' '.join(memdef.find('detaileddescription').itertext())
            detaileddescription = detaileddescription.strip().replace('\n', '\n\t\t')
            params = []
            # params = memdef.findall('param')
            for param in memdef.findall('param'):
                declname = param.find('declname')
                if declname is None: continue
                pname = declname.text
                ptype = ' '.join(param.find('type').itertext())
                pt, m = getTypeNameFromCPPType(ptype, moduleName)
                if m: importModules[m] = None
                params.append('{}: {} = ...'.format(pname, pt))
            
            funcCode = '\tdef '
            if isStatic:
                funcCode = '\t@staticmethod\n' + funcCode + funcName + '('
            else:
                funcCode += funcName + '(self'

            if funcName in funcNames:
                funcCode = '\t@typing.overload\n' + funcCode
            else:
                funcNames[funcName] = None

            if params:
                if not isStatic:
                    funcCode += ', '
                funcCode += ', '.join(params)
                # funcCode += ', *args: typing.Any'
                funcCode += ', **kwargs: typing.Any'
            
            rts, m = getReturnType(returnType)
            if m: importModules[m] = None
            funcCode += ') -> {}:\n'.format(rts)
            funcCode += "\t\t'''{}\n\t\t'''\n\n".format(detaileddescription)

            code += funcCode.expandtabs(4)
        elif kind == 'enum' and isPublic:
            ecode, enames = getClassEnumFromXml(memdef)
            enumCode += ecode
            enumCode += '\n\n'
            enumNames.update(enames)
        elif kind == 'variable' and isPublic:
            mutable = memdef.attrib['mutable'] == 'yes'
            name = memdef.find('name').text
            rt = memdef.find('type').text
            rts, m = getReturnType(rt)
            if m: importModules[m] = None
            if isStatic:
                variableCode += '\t{}: typing.ClassVar[{}] = ...\n\n'.format(name, rts)
            else:
                getCode = '\t@property\n'
                getCode += '\tdef {}(self) -> {}: ...\n'.format(name, rts)
                variableCode += getCode
                if mutable:
                    setCode = '\t@{}.setter\n'.format(name)
                    setCode += '\tdef {}(self, v: {}) -> None: ...\n'.format(name, rts)
                    variableCode += setCode
        elif kind == 'typedef' and isPublic:
            # TODO type al
            pass
        else:
            if isPublic:
                print(kind)
                # if kind == 'variable':
                #     print('-'*150)
                #     print(xmlDoc)
            pass
            # print(kind)
            # if kind == 'variable':
            #     print('-'*150)
            #     print(xmlDoc)

    code += variableCode.expandtabs(4) + '\n'
    code += enumCode
    if code.strip().endswith('):'):
        code = code.replace('):', '):...\n\n')
    
    # code += '\n\n'
    return (code, importModules)

def getClassPyi(clsName: str, cls: typing.Type, parentClass: str) -> str:
    code = 'class {}({}):\n\n'.format(clsName, parentClass)
    code += '\tdef __init__(self, *args, **kws) -> None: ...\n'
    funcCodeTemp = '\tdef {}('
    clsAttrs = '\n\n'
    members = inspect.getmembers(cls)
    for member in members:
        name, mtype = member
        # skip
        if name.startswith('__') and name.endswith('__'): continue
        if inspect.isdatadescriptor(mtype) or hasattr(mtype, "fget"):
            rt = 'typing.Any'
            getCode = '\t@property\n'
            getCode += funcCodeTemp.format(name)
            getCode += 'self) -> {}: ...\n'.format(rt)
            code += getCode
            if hasattr(mtype, "fset") and mtype.fset is None:
                setCode = '\t@{}.setter\n'.format(name)
                setCode += funcCodeTemp.format(name)
                setCode += 'self, v: {}) -> None: ...\n'.format(rt)
                code += setCode
        elif inspect.ismethoddescriptor(mtype):
            # if not name.startswith('__') and not name.endswith('__'):
            funcCode = '\t@classmethod\n\t'
            funcCode += emptyFuncStr(name).replace('*args', 'cls, *args')
            code += funcCode
        else:
            # if not name.startswith('__') and not name.endswith('__'):
            clsAttrs += '\t{}: typing.ClassVar[{}] = ...\n'.format(name, type(mtype).__name__)

    code += clsAttrs
    if code.strip().endswith('):'):
        code += '...'
    code += '\n\n'
    return code.expandtabs(4)

def emptyClass(name: str) -> str:
    clsPYI = 'class {}(object): ...\n\n'.format(name)
    return clsPYI

def emptyFuncStr(name: str) -> str:
    out = 'def {}(*args, **kws) -> typing.Any: ...\n'.format(name)
    return out

def getXmlDoc(moduleName: str, clsName: str, docTemp: str) -> str:
    xmlDoc = docTemp.format(getXmlName(moduleName, clsName))
    if os.path.exists(xmlDoc):
        return xmlDoc
    for i in pxr.__all__:
        xml = docTemp.format(getXmlName(i, clsName))
        if os.path.exists(xml):
            return xml
    return xmlDoc

def writePYI(moduleName: str, docTemp: str, pyiOutDir: str = ''):
    importModules = {}
    
    fullModuleName = 'pxr.'+moduleName
    module = importlib.import_module(fullModuleName)
    members = inspect.getmembers(module)

    pyiPath, ext = os.path.splitext(os.path.abspath(module.__file__))
    if pyiOutDir:
        names = fullModuleName.split('.')
        names.append('__init__')
        pyiPath = os.path.join(pyiOutDir, *names)
        if not os.path.exists(os.path.dirname(pyiPath)):
            os.makedirs(os.path.dirname(pyiPath))
    pyiPath += '.pyi'

    mcode = ''
    funcCode = ''
    properties = ''
    for member in members:
        name, mtype = member
        if inspect.isclass(mtype):
            baseClasses = inspect.getmro(mtype)
            pclass = getParentClassName(baseClasses[1].__name__, baseClasses[1])
            # xmlDoc = docTemp.format(getXmlName(moduleName, name))
            xmlDoc = getXmlDoc(moduleName, name, docTemp)
            if os.path.exists(xmlDoc):
                classCode, ims = getClassPyiFromXml(name, xmlDoc, pclass, moduleName)
                importModules.update(ims)
                mcode += classCode
            else:
                # print('no xml doc: {}'.format(xmlDoc), name)
                # mcode += emptyClass(name)
                mcode += getClassPyi(name, mtype, pclass)
        elif inspect.isfunction(mtype):
            funcCode += emptyFuncStr(name)
        elif inspect.isdatadescriptor(mtype) or hasattr(mtype, "fget"):
            # hasattr(prop, "fset") and prop.fset is None
            properties += '{}: {} = ...\n'.format(name, type(mtype).__name__)
        elif inspect.isbuiltin(mtype):
            funcCode += emptyFuncStr(name)
        else:
            pass

    imStr = ''
    for m in importModules:
        if m: imStr += 'import {}\n'.format(m)
    code = imStr + '\n\n' + mcode
    code = 'import typing\n\n' + code
    code = 'from __future__ import annotations\n' + code
    code += '\n\n' + funcCode
    code += '\n\n' + properties
    with open(pyiPath, 'w') as pyi:
        pyi.write(code)

    return pyiPath

def genUsdStubs(helpDir: str = '', pyiOutDir: str = None):
    import maya.cmds
    maya.cmds.loadPlugin('mayaUsdPlugin')

    # import pxr
    global pxr
    pxr = importlib.import_module('pxr')

    docTemp = os.path.join(helpDir, "class{}.xml")
    for m in pxr.__all__:
        pyi = writePYI(m, docTemp, pyiOutDir)

        print('{} done!'.format(pyi))

def genFromStandalone():
    import maya.standalone as ms

    ms.initialize('python')

    helpDir = "E:\\coding\\libs\\usd_build\\docs\\doxy_xml"
    # pyiDir = os.path.join(os.path.dirname(__file__), 'pyi')
    pyiDir = None
    genUsdStubs(helpDir, pyiDir)

    # members = inspect.getmembers(pxr.Usd.Tokens)
    # # members = inspect.getmembers(pxr.Usd.StageLoadRules)
    # md = []
    # md_ = []
    # m = []
    # f = []
    # dd = []
    # clsPro = []
    # for i in members:
    #     name, t_ = i
    #     if inspect.isfunction(t_):
    #         f.append(i)
    #     elif inspect.ismethod(t_):
    #         m.append(i)
    #     elif inspect.isdatadescriptor(t_):
    #         dd.append(i)
    #     elif inspect.ismemberdescriptor(t_):
    #         md_.append(i)
    #     elif inspect.ismethoddescriptor(t_):
    #         md.append(i)
    #     else:
    #         clsPro.append(i)

    # def get_type_fullname(typ: type) -> str:
    #     return f"{typ.__module__}.{getattr(typ, '__qualname__', typ.__name__)}"

    ms.uninitialize()
    # sys.exit()

def onMayaDroppedPythonFile(obj):
    if os.path.exists(docsConfig.Paths.USD_XML):
        genUsdStubs(docsConfig.Paths.USD_XML, docsConfig.Paths.PYI_DIR)
