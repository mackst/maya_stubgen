# -*- coding: utf-8 -*-

# 作者：石池

from html.parser import HTMLParser
import importlib
import inspect
import io
import keyword
import os
import re
import sys
import pprint
import typing

import docsConfig
import api1_stubgen


class BaseMemItem(object):

    def __init__(self) -> None:
        self.name = ''
        self.isStatic = False
        self.description = ''


class MethodMemItem(BaseMemItem):

    def __init__(self) -> None:
        super().__init__()
        self.doc = ''
        self.signature = ''
        self.parameters = ''
        self.returns = ''

    def __str__(self) -> str:
        d = {}
        d[self.name] = (self.isStatic, self.doc, self.signature, self.parameters, self.returns, self.description)

        return str(d)
    
    __repr__ = __str__


class DataMemItem(BaseMemItem):

    def __init__(self) -> None:
        super().__init__()
        self.type = ''

    def __str__(self) -> str:
        d = {}
        d[self.name] = (self.isStatic, self.type, self.description)

        return str(d)
    
    __repr__ = __str__


class PropertyMemItem(DataMemItem):

    def __init__(self) -> None:
        super().__init__()
        self.access = ''
        self.doc = ''

    def __str__(self) -> str:
        d = {}
        d[self.name] = (self.isStatic, self.doc, self.type, self.access, self.description)

        return str(d)
    
    __repr__ = __str__


class ApiClassParaser(HTMLParser):

    def __init__(self) -> None:
        super().__init__()

        self.classAttributes = ''
        self.classProperties = ''
        self.docString = ''

        self.__docStrStart = False

        self.__constructorTableStart = False
        self.__constructorStart = False
        self.__constructorTRStart = False
        self.__constructorTRCount = 0
        self.__constructorTDStart = False
        self.__constructorDocStart = False
        self.__constructorInToMethod = False

        self.__memberFuncStart = False
        self.__memberDataStart = False
        self.__propertyStart = False

        self.__memitemStart = False
        self.__memitemStaticStart = False
        self.__memitemNameStart = False
        self.__memitemDocStart = False
        self.__memitemDocTableStart = False
        self.__memitemSignatureStart = False
        self.__memitemParametersStart = False
        self.__memitemReturnsStart = False
        self.__memitemTypeStart = False
        self.__memitemAccessStart = False
        self.__memitemDescriptionStart = False

        self._resetMemItem()

        # self.__initFuncs = []
        # self.__initFuncDoc = ''
        self.__initTDStr = ''
        self.__initTDs = []
        
        # self.methods = {}
        # Constructors
        self.constructors = {}
        self.memitems = []

    def _resetMemItem(self):
        self.__memitemName = ''
        self.__memitemStatic = False
        self.__memitemDoc = ''
        self.__memitemSignature = ''
        self.__memitemParameters = ''
        self.__memitemReturns = ''
        self.__memitemType = ''
        self.__memitemAccess = ''
        self.__memitemDescription = ''

    def _pushMethodMemItem(self):
        item = MethodMemItem()
        item.name = self.__memitemName
        item.isStatic = self.__memitemStatic
        item.doc = self.__memitemDoc
        item.signature = self.__memitemSignature
        item.parameters = self.__memitemParameters
        item.returns = self.__memitemReturns
        item.description = self.__memitemDescription
        self.memitems.append(item)

        self._resetMemItem()

    def _pushDataMemItem(self):
        item = DataMemItem()
        item.name = self.__memitemName
        item.type = self.__memitemType
        item.description = self.__memitemDescription

        self.memitems.append(item)

        self._resetMemItem()

    def _pushPropertyMemItem(self):
        item = PropertyMemItem()
        item.name = self.__memitemName
        item.doc = self.__memitemDoc
        item.type = self.__memitemType
        item.access = self.__memitemAccess
        item.description = self.__memitemDescription

        self.memitems.append(item)

        self._resetMemItem()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == 'div' and ('class', 'textblock') in attrs:
            self.__docStrStart = True
            return

        # if tag == 'table' and ('class', 'ruled') in attrs:
        #     self.__constructorTableStart = True
        #     return

        if tag == 'tr' and self.__constructorTableStart:
            self.__constructorTRStart = True
            return

        if tag == 'td' and self.__constructorTableStart:
            # self.__constructorStart = True
            self.__constructorTDStart = True
            return
        
        # if tag == 'td' and self.__constructorTableStart:
        #     self.__constructorTDStart = True
        #     return

        # if tag == 'p' and ('class', 'starttd') in attrs and self.__constructorStart:
        #     # self.__constructorStart = False
        #     self.__constructorDocStart = True
        #     return

        if tag == 'div' and ('class', 'memitem') in attrs and self.__memberFuncStart:
            self.__memitemStart = True
            return
        
        if tag == 'div' and ('class', 'memitem') in attrs and self.__memberDataStart:
            self.__memitemStart = True
            return
        
        if tag == 'div' and ('class', 'memitem') in attrs and self.__propertyStart:
            self.__memitemStart = True
            return

        if tag == 'table' and ('class', 'memname') in attrs and self.__memitemStart:
            self.__memitemNameStart = True
            return
        
        if tag == 'span' and ('class', 'mlabel') in attrs and self.__memitemStart:
            self.__memitemStaticStart = True
            return
        
        if tag == 'div' and ('class', 'memdoc') in attrs and self.__memitemStart:
            self.__memitemDocTableStart = True
            return

        if tag == 'pre' and ('class', 'fragment') in attrs and self.__memitemStart:
            self.__memitemDocStart = True
            return

    def handle_endtag(self, tag: str) -> None:
        if tag == 'pre' and self.__docStrStart:
            self.__docStrStart = False
            return
        
        if tag == 'td' and self.__constructorTDStart:
            self.__constructorTDStart = False
            self.__initTDs.append(self.__initTDStr)
            self.__initTDStr = ''
            return
        
        if tag == 'tr' and self.__constructorTRStart:
            self.__constructorTRStart = False
            if len(self.__initTDs) == 3:
                # initFuncArg = ' '.join(self.__initTDs[1:-1])
                self.constructors[self.__initTDs[0].strip()] = (self.__initTDs[1].strip(), self.__initTDs[2].strip())
                # print(self.__initTDs)
            self.__initTDs = []
            self.__initTDStr = ''
            return

        if tag == 'table' and self.__constructorTableStart:
            self.__constructorTableStart = False
            return

        # if tag == 'p' and self.__constructorDocStart:
        #     self.__constructorDocStart = False
        #     self.__constructorInToMethod = True
        #     self.__constructorStart = False
        #     return

        if tag == 'table' and self.__memitemNameStart:
            self.__memitemNameStart = False
            return
        
        if tag == 'span' and self.__memitemStaticStart:
            self.__memitemStaticStart = False
            return
        
        if tag == 'div' and self.__memitemDocTableStart:
            self.__memitemStart = False
            self.__memitemDocTableStart = False
            self.__memitemSignatureStart = False
            self.__memitemParametersStart = False
            self.__memitemReturnsStart = False
            self.__memitemDescriptionStart = False
            self.__memitemTypeStart = False
            self.__memitemAccessStart = False
            if self.__memberFuncStart:
                self._pushMethodMemItem()
            if self.__memberDataStart:
                self._pushDataMemItem()
            if self.__propertyStart:
                self._pushPropertyMemItem()
            return
        
        if tag == 'pre' and self.__memitemDocStart:
            self.__memitemDocStart = False
            return

    def handle_data(self, data: str) -> None:
        if data == 'Constructors':
            self.__constructorTableStart = True

        if data == 'Member Function Documentation':
            self.__memberFuncStart = True

        if data == 'Member Data Documentation':
            self.__memberFuncStart = False
            self.__memberDataStart = True

        if data == 'Property Documentation':
            self.__memberFuncStart = False
            self.__memberDataStart = False
            self.__propertyStart = True

        if data == 'Signature:' and self.__memitemDocTableStart:
            self.__memitemSignatureStart = True

        if data == 'Parameters:' and self.__memitemDocTableStart:
            self.__memitemSignatureStart = False
            self.__memitemParametersStart = True

        if data == 'Returns:' and self.__memitemDocTableStart:
            self.__memitemParametersStart = False
            self.__memitemReturnsStart = True
        
        if data == 'Type:' and self.__memitemDocTableStart:
            self.__memitemTypeStart = True

        if data == 'Access:' and self.__memitemDocTableStart:
            self.__memitemTypeStart = False
            self.__memitemAccessStart = True

        if data == 'Description:' and self.__memitemDocTableStart:
            self.__memitemTypeStart = False
            self.__memitemAccessStart = False
            self.__memitemReturnsStart = False
            self.__memitemDescriptionStart = True

        # -----------------------------------------------------------------------
        if self.__docStrStart:
            self.docString += data

        # if self.__constructorStart:
        #     self.__initFuncs.append(data)

        if self.__constructorTDStart:
            self.__initTDStr += data

        # if self.__constructorDocStart:
        #     self.__initFuncDoc += data

        # if self.__constructorInToMethod:
        #     if self.__initTDs:
        #         # print(self.__initTDs)
        #         pass
        #     if self.__initFuncs:
        #         initFuncArg = ' '.join(self.__initFuncs[1:])
        #         initFuncArg = initFuncArg.replace(self.__initFuncDoc, '')
        #         clsName = self.__initFuncs[0]
        #         if ')' not in clsName:
        #             clsName += self.__initFuncs[1]
        #             initFuncArg = ' '.join(self.__initFuncs[2:-1])
        #         # self.constructors[clsName] = (initFuncArg, self.__initFuncDoc)
        #         # self.constructors[clsName] = initFuncArg

        #     # print(self.__initFuncs)
        #     self.__initFuncs = []
        #     self.__initFuncDoc = ''
        #     self.__constructorInToMethod = False

        if self.__memitemNameStart:
            self.__memitemName += data

        if self.__memitemStaticStart:
            self.__memitemStatic = data == 'static'
        
        if self.__memitemDocStart:
            self.__memitemDoc += data

        if self.__memitemSignatureStart:
            self.__memitemSignature += data

        if self.__memitemParametersStart:
            self.__memitemParameters += data

        if self.__memitemReturnsStart:
            self.__memitemReturns += data

        if self.__memitemTypeStart:
            self.__memitemType += data

        if self.__memitemAccessStart:
            self.__memitemAccess += data

        if self.__memitemDescriptionStart:
            self.__memitemDescription += data

    @property
    def testdata(self):
        return self.__initTDs




APIModuleDocNames = {
    'maya.api.OpenMaya': 'open_maya',
    'maya.api.OpenMayaAnim': 'open_maya_anim',
    'maya.api.OpenMayaRender': 'open_maya_render',
    'maya.api.OpenMayaUI': 'open_maya_u_i',
}


ConstructorTypes = {}

def getClassLowerName(name: str) -> str:
    uppers = [c for c in name if c.isupper()]
    x = name
    for u in uppers:
        x = x.replace(u, '_'+u.lower())

    return x

def getConstructorTypes(typeStr: str, className: str = '') -> str:
    builtinTypes = {
        '': str.__name__,
        'none': 'None',
        'string': str.__name__,
        'float': float.__name__,
        'int': int.__name__,
        'long': int.__name__,
        'bool': bool.__name__,
        'boolean': bool.__name__, 
        'true': bool.__name__,
        'false': bool.__name__,
        'bytearray': bytearray.__name__,
    }
    
    lower = typeStr.lower()
    if lower in builtinTypes:
        return builtinTypes[lower]
    
    if lower.startswith('list of str'):
        return 'list[str]'

    if lower.startswith('list of'):
        return 'list'
    
    if lower.startswith('sequence of str'):
        return 'list[str]'
    
    if lower.startswith('sequence of'):
        return 'list'
    
    if lower.startswith('tuple of str'):
        return 'tuple[str]'
    
    if lower.startswith('tuple of'):
        return 'tuple'
    
    if lower == 'self' or lower.endswith('to self') or lower.endswith('to self.'):
        if className:
            return className
        return 'self'
    
    # if lower.endswith('type constant'):
    if lower.endswith(' constant'):
        return int.__name__
    
    if typeStr.startswith('M'):
        t = typeStr.replace(' or ', ', ')
        if ',' in t:
            ts = t.split(',')
            types = [getConstructorTypes(i.replace(')', '').replace('.', '').strip(), className) for i in ts]
            return 'typing.Union[{}]'.format(', '.join(types))
        elif '::' in t:
            return 'typing.Callable'
        elif '<' in t:
            return t.split('<')[0]
        elif t.startswith('MFn '):
            return 'int'
        else:
            # om.MFn.__module__
            # OpenMaya
            tss = typeStr.strip()
            tss = tss.split(')')[0].strip()
            if tss == 'MString': return str.__name__
            if tss == 'MImageFilterFormat': return int.__name__
            if tss == 'MStatus': return 'typing.Any'
            return tss
    
    if typeStr.startswith('(') and typeStr.endswith(')'):
        typeStr = typeStr.replace('(', '').replace(')', '')
        if ',' in typeStr:
            ts = typeStr.split(',')
            types = [getConstructorTypes(i.strip(), className) for i in ts]
            return 'tuple[{}]'.format(', '.join(types))
        else:
            return 'tuple'

    if typeStr.startswith('[') and typeStr.endswith(']'):
        # if typeStr == '[Float, Float, Float, Float]':
        #     pass
        typeStr = typeStr.replace('[', '').replace(']', '')
        if ',' in typeStr:
            ts = typeStr.split(',')
            types = [getConstructorTypes(i.strip(), className) for i in ts]
            return 'list[{}]'.format(', '.join(types))
        else:
            return 'list'
        
    if typeStr.startswith('k'):
        if typeStr[1].isupper():
            return '{}.{}'.format(className, typeStr)
        
    return 'typing.Any'

def getParameterInfoFromCpp(items: list[str]):
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

    return (pName, pType)

def getClassConstructorFromCpp(className: str, htmlDoc: str):
    if className == 'MUintArray':
        pass
    docDir = os.path.dirname(htmlDoc)
    docDir = os.path.dirname(docDir)
    classDoc = os.path.join(docDir, 'cpp_ref', 'class{}.html'.format(getClassLowerName(className)))
    if not os.path.exists(classDoc):
        return '    def __init__(self, *args, **kws) -> None: ...\n'
    paraser = api1_stubgen.Api1ClassParaser()
    with open(classDoc) as f:
        paraser.feed(f.read())
    constructorItems = paraser.constructorItems

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
            code += "        ''''''\n\n"
        else:
            code = codeTemp
            # Parameters
            paramStr = name.split('(')[1].split(')')[0].strip()
            if paramStr:
                parameters = paramStr.split(',')
                for para in parameters:
                    pType = ''
                    pName = ''
                    paraStr = para.strip()
                    if '=' in paraStr:
                        paraStr = paraStr.split('=')[0].strip()
                    
                    paraStr = paraStr.replace('&', '').replace('*', '')
                    pstrs = [i.strip() for i in paraStr.split(' ') if i.strip()]
                    pName, pType = getParameterInfoFromCpp(pstrs)
                    # skip MStatus
                    if pType == 'MStatus': continue
                    
                    code += ', {}: {} = ...'.format(pName, getConstructorTypes(pType))
                code += ') -> None:\n'
                doc = itemData.doc.replace('\nParameters', '\n\n`Parameters:`').strip()
                doc = doc.replace('\n', '\n\t\t').expandtabs(4)
                code += "        '''{}\n        '''\n\n".format(doc)
            else:
                code = codeTemp + ', *args, **kws) -> None:\n'
                code += "        ''''''\n\n"
        if index != 0:
            code = '    @typing.overload\n' + code

        pyi += code
    return pyi

def getClassConstructorStr(constructors: dict, className: str = ''):
    # global ConstructorTypes

    out = ''

    for id, i in enumerate(constructors):
        type_, doc = constructors[i]
        type_ = type_.strip()
        doc = doc.strip()

        overload = '    @typing.overload\n'
        temp = '    def __init__(self'
        if id != 0: temp = overload + temp
        if type_:
            types = type_.split('\n')
            for t_ in types:
                if ' - ' not in t_: continue
                tn, tstr = t_.split('-')
                tn = tn.strip()
                tstr = tstr.strip()
                temp += ', {}: {} = ...'.format(tn, getConstructorTypes(tstr, className))
                # ConstructorTypes[tstr.strip()] = ''
        
        temp += ') -> None:\n'
        if doc:
            temp += "        '''{}'''\n\n".format(doc)
        
        out += temp

    # if not out:
    #     out = "    def __init__(self) -> None:\n        ''''''\n\n"

    return out


MagiceFunctionReturnTypes = {
    '__repr__': str.__name__,
    '__str__': str.__name__,
    '__eq__': bool.__name__,
    '__ge__': bool.__name__,
    '__gt__': bool.__name__,
    '__le__': bool.__name__,
    '__lt__': bool.__name__,
    '__ne__': bool.__name__,
    # '__str__': str.__name__,
    # '__str__': str.__name__,
    # '__str__': str.__name__,
    # '__str__': str.__name__,
}

def getInfoFromDocStr(methodName: str, docStr: str, className: str = '') -> tuple:
    if className == 'MSelectionList' and methodName == 'add':
        pass
    out = []
    spattern = '{}\((.*)\) -> (\w+)'.format(methodName)
    pp = ' {} \((.*)\) - (.*)\\n?'
    pp = '\* {} \((.*)\) - '

    ptemp = '{}: {} = ...'
    sigInfo = re.findall(spattern, docStr.replace(methodName+'(', '\n'+methodName+'('))
    for sig in sigInfo:
        paramStr = sig[0]
        parameters_ = []

        complexParams = False
        pname = ''
        if '(' in paramStr and ')' in paramStr:
            pname = paramStr.split('(')[0].replace(',', '').replace(' ', '_')
            pname = pname.split('=')[0]
            pname = '*args: typing.Any, ' + pname + ': tuple = ...' 
            complexParams = True
        elif '(' not in paramStr and ')' in paramStr:
            paramStr = paramStr.replace(')', '')
        if '[' in paramStr and ']' in paramStr:
            pname = paramStr.split('[')[0].replace(',', '').replace(' ', '_')
            pname = pname.split('=')[0]
            if pname:
                pname = '*args: typing.Any, ' + pname + ': list = ...'
            complexParams = True

        # if '=' in paramStr:
        #     paramStr = paramStr.split('=')[0]
        #     if ',' in paramStr:
        #         parameters_.append('*args: typing.Any')
        
        if complexParams:
            parameters_.append(pname)
        else:
            params = paramStr.split(',')
            for p in params:
                p_ = p.strip()
                paramInfo = re.search(pp.format(p_), docStr)
                if paramInfo:
                    if keyword.iskeyword(p_):
                        p_ += '_'
                    tstr = paramInfo.groups()[0].split(')')[0]
                    pt_ = getConstructorTypes(tstr, className)
                    pstr = ptemp.format(p_, pt_)
                    parameters_.append(pstr)
        
        returnType = ''
        if sig[1].lower() == 'self':
            returnType = className
        else:
            returnType = getConstructorTypes(sig[1], className)

        out.append((parameters_, returnType))

    return out

def memItemProcess(items: list, className: str = ''):
    # debug
    if className == 'MCallbackId':
        pass

    global MagiceFunctionReturnTypes

    # out = {}
    out = ''
    staticCodeTemp = '\t@staticmethod\n'
    staticCodeTemp += '\tdef {}('
    codeTemp = '\tdef {}(self'

    methods = []
    properties = []
    datas = {}
    for i in items:
        if not i.name.strip(): continue
        if isinstance(i, MethodMemItem):
            # skip __new__
            if '__new__' in i.name: continue
            mdocString = "\t\t'''\n"
            mdocString += "\t\t" + i.doc.strip().replace('\n', '\n\t\t') + '\n\n'
            methodStr_ = codeTemp
            if i.isStatic:
                methodStr_ = staticCodeTemp
            parameters_ = {}
            parameters = i.parameters.strip()
            complexParameters = False
            methodStrs = []
            if parameters:
                if ' - ' in parameters:
                    parameters = parameters.split('Parameters:')[1:]
                    for pid, par_ in enumerate(parameters):
                        parameterStrs = []
                        param = par_.strip().split('\n')
                        for p in param:
                            if not p.strip(): continue
                            pname, ptype = p.split('-')
                            pt = getConstructorTypes(ptype.strip(), className)
                            parameterStrs.append('{}: {} = ...'.format(pname.strip(), pt))
                        parameters_[pid] = parameterStrs
                else:
                    xx = parameters.replace('Parameters:', '').strip()
                    if xx:
                        complexParameters = True

            methodName = i.name.replace('\n', '').replace(' ', '').split('.')[-1].split('()')[0]
            if methodName == 'merge':
                pass
            # return type
            returnTypes = {}
            if methodName in MagiceFunctionReturnTypes:
                returnTypes[0] = MagiceFunctionReturnTypes[methodName]
            else:
                rt = i.returns.strip()
                if rt:
                    rts = rt.split('Returns:')[1:]
                    for tid, t_ in enumerate(rts):
                        # if not t_.strip():
                        #     returnTypes[tid] = []
                        #     continue
                        returnTypes[tid] = getConstructorTypes(t_.strip(), className)
                else:
                    returnTypes[0] = 'None'

            # methodName = ''
            signature = i.signature.strip()
            if signature:
                signatures_ = signature.split('Signature:')[1:]
                # if signature:
                for sid, signature in enumerate(signatures_):
                    methodStr = methodStr_
                    if sid != 0:
                        methodStr = '\t@typing.overload\n' + methodStr_
                    
                    methodName, b_ = signature.split('(')
                    methodName = methodName.strip()
                    methodStr = methodStr.format(methodName)
                    if complexParameters:
                        parameters = b_.strip()[:-1].split(',')
                        funcParams = []
                        for param in parameters:
                            if ' ' in param.strip():
                                xparams = param.split(' ')
                                if xparams[0][0].isupper():
                                    funcParams.append('{}: {} = ...'.format(xparams[1], xparams[0]))
                                else:
                                    funcParams.append('{}: {} = ...'.format(xparams[0], xparams[1]))
                            elif '=' in param:
                                zparam, pt = param.strip().split('=')
                                funcParams.append('{}: {} = ...'.format(zparam, getConstructorTypes(pt, className)))
                                pass
                            else:
                                ps = param.strip()
                                if ps:
                                    funcParams.append(ps + ': typing.Any = ...')
                        if funcParams:
                            if methodStr.endswith('(self'):
                                methodStr += ', '
                            methodStr += ', '.join(funcParams)
                    else:
                        if parameters_:
                            pstr = ', '.join(parameters_[sid])
                            methodStr += ', ' + pstr
                    methodStr += ') -> {}:\n'.format(returnTypes.get(sid, 'None'))
                    methodStrs.append(methodStr)
            else:
                methodStr = methodStr_.format(methodName)
                if parameters_:
                    methodStr += ', '.join(parameters_[0])
                if not parameters_ and i.doc.strip():
                    docInfo = getInfoFromDocStr(methodName, i.doc.strip(), className)
                    if docInfo:
                        anyTstr = '*args: typing.Any'
                        pstr = ', '.join(docInfo[0][0])
                        if len(docInfo) > 1:
                            # methodStr += ', '
                            if anyTstr not in pstr:
                                methodStr += ', ' + anyTstr
                        if pstr:
                            if methodStr.endswith('(self') or methodStr.endswith(anyTstr):
                                methodStr += ', '
                            methodStr += pstr
                        hasRT = False
                        if returnTypes:
                            hasRT = returnTypes[0] != 'None'
                        if docInfo[0][1] and not hasRT:
                            returnTypes[0] = docInfo[0][1]
                if returnTypes:
                    methodStr += ') -> {}:\n'.format(returnTypes[0])
                else:
                    methodStr += '):\n'
                
                methodStr = methodStr.replace('(,', '(', 1)
                methodStrs.append(methodStr)
            
            if i.signature.strip():
                mdocString += '\t\t' + i.signature.replace('Signature', '`Signature`').replace('\n', '\n\t\t') + '\n\n'
            if i.parameters.strip():
                mdocString += '\t\t' + i.parameters.replace('Parameters', '`Parameters`').replace('\n', '\n\t\t').strip() + '\n\n'
            if i.returns.strip():
                mdocString += '\t\t' + i.returns.replace('Returns', '`Returns`').replace('\n', '\n\t\t') + '\n\n'
            if i.description.strip():
                mdocString += '\t\t' + i.description.replace('Description', '`Description`').replace('\n', '\n\t\t') + '\n\n'
            mdocString += "\t\t'''\n\n"

            for ms in methodStrs:
                ms_ = ms + mdocString.expandtabs(4)
                methods.append(ms_)
            # print(methodStr)
            # print('-'*120)
        elif isinstance(i, PropertyMemItem):
            if className == 'MArgParser':
                pass
            docString = "\t\t'''\n"
            # @property
            pcode = ''
            tempCode = '\tdef {}(self'
            getCode = '\t@property\n' + tempCode
            setCode = '\t@{}.setter\n' + tempCode

            name = i.name.strip().split('.')[-1]
            t_ = 'None'
            if i.type.strip():
                ts_ = i.type.split(':')[1].strip()
                t_ = getConstructorTypes(ts_, className)
            getCode = getCode.format(name) + ') -> ' + t_ + ' :\n'
            docString += '\t\t{}\n\n'.format(i.doc)
            docString += '\t\t' + i.type.replace('Type', '`Type`')# + '\n'
            docString += '\t\t' + i.access.replace('Access', '`Access`')# + '\n'
            docString += '\t\t' + i.description.replace('Description', '`Description`')# + '\n'
            docString += "\t\t'''\n\n"
            getCode += docString
            pcode += getCode
            if i.access:
                if i.access.split(':')[1].strip() == 'RW':
                    setCode = setCode.format(name, name)
                    setCode += ') -> None :\n'
                    setCode += docString
                    pcode += setCode
            
            # print(pcode)
            properties.append(pcode)
        
        elif isinstance(i, DataMemItem):
            desc = i.description.strip()
            if desc:
                nstr = i.name.strip().split('=')[0]
                nstr = nstr.strip().split('.')[-1]
                datas[nstr.strip()] = desc
    
    out += ''.join(methods)
    out += ''.join(properties)
    # print(datas)
    # print('-'*120)
    return (out, datas)

def getClassPYI(className: str, htmlDoc: str, class_: typing.Any):
    docString = "\t'''\n"
    docString += "\t{}\n"
    spaStr = "\t### Static Public Attributes\n"
    docStringEnd = "\t'''\n\n"
    baseClasses = inspect.getmro(class_)
    # bclsStr = ', '.join([cls.__name__ for cls in baseClasses[1:]])

    members = inspect.getmembers(class_)

    paraser = None
    with open(htmlDoc) as f:
        paraser = ApiClassParaser()
        paraser.feed(f.read())

    clsPYI = 'class {}({}):\n\n'.format(className, baseClasses[1].__name__)

    # Constructors
    cstr = getClassConstructorStr(paraser.constructors, className)
    if not cstr:
        cstr = getClassConstructorFromCpp(className, htmlDoc)
        if not cstr:
            cstr = "    def __init__(self, *args, **kws) -> None:\n        ''''''\n\n"

    # memitems 
    methods, attrData = memItemProcess(paraser.memitems, className)

    # class attributes
    clsAttrStr = ''
    for member in members:
        memName = member[0]
        if memName.startswith('k') and memName[1].isupper():
            tn = type(member[1]).__name__
            x = '    {}: {} = ...\n'.format(memName, tn)
            clsAttrStr += x
            clsAttrDoc = attrData.get(memName, '')
            spaStr += '\t\t`{}` : `{}`\n\t\t\t {}\n'.format(memName, tn, clsAttrDoc)
    
    # doc string
    dstr = '\t' + paraser.docString.replace('\n', '\n\t\t') + '\n\n'
    docString = docString.format(dstr+spaStr)
    docString += docStringEnd
    clsPYI += docString.expandtabs(4)

    if clsAttrStr: clsAttrStr += '\n'
    clsPYI += clsAttrStr

    clsPYI += cstr
    clsPYI += methods.expandtabs(4)

    # print(clsPYI)
    return clsPYI


def emptyFuncStr(name: str) -> str:
    out = 'def {}(*args, **kws) -> typing.Any: ...\n\n'.format(name)
    return out

def writePYI(module: typing.Any, htmlTemp: str, pyiPath: str):
    # mFile = module.__file__
    mDocName = APIModuleDocNames[module.__name__]
    members = inspect.getmembers(module)

    classStr = 'from __future__ import annotations\nimport typing\n\n'
    if mDocName != 'open_maya':
        classStr += 'from maya.api.OpenMaya import *\n\n'
    funcStr = ''
    for member in members:
        name, mtype = member
        if inspect.isclass(mtype):
            docName = '{}_1_1{}'.format(mDocName, getClassLowerName(name))
            htmlDoc = htmlTemp.format(docName)
            # assert(os.path.exists(htmlDoc))
            if not os.path.exists(htmlDoc):
                print(f'{name} - {htmlDoc} : not exists')
                continue
            classStr += getClassPYI(name, htmlDoc, mtype)
            # break
        elif inspect.isfunction(mtype):
            funcStr += emptyFuncStr(name)
        elif inspect.isbuiltin(mtype):
            funcStr += emptyFuncStr(name)
        else:
            # om_others.append(i)
            # print(name, type(mtype))
            pass
    
    classStr += '\n\n' + funcStr
    with open(pyiPath, 'w') as pyi:
        pyi.write(classStr)

def genStandaloneStubs(pyiOutDir: str = None):
    m = 'maya.standalone'
    module = importlib.import_module(m)

    pyiPath, ext = os.path.splitext(os.path.abspath(module.__file__))
    if pyiOutDir:
        names = m.split('.')
        pyiPath = os.path.join(pyiOutDir, *names)
        if not os.path.exists(os.path.dirname(pyiPath)):
            os.makedirs(os.path.dirname(pyiPath))
    pyiPath += '.pyi'

    code = 'def initialize(name: str = "python") -> None:\n'
    code += "    '''" + module.initialize.__doc__
    code += "    '''\n\n"
    code += 'def uninitialize() -> None: ... \n'

    with open(pyiPath, 'w') as pyi:
        pyi.write(code)

    print('{} done.'.format(pyiPath))

def genAIP20Stubs(helpDir: str = '', pyiOutDir: str = None, modules: typing.Iterable = None):
    if not helpDir:
        return
    
    pyRefDir = os.path.join(helpDir, 'py_ref')
    if not os.path.exists(pyRefDir):
        return
    
    htmlTemp = os.path.join(pyRefDir, 'class_{}.html')

    if not modules:
        modules = APIModuleDocNames

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

    genStandaloneStubs(pyiOutDir)


def genFromStandalone():
    docDir = 'E:\\coding\\docs\\maya-2024-developer-help-enu'

    import maya.standalone as ms

    ms.initialize('python')

    # pyiDir = os.path.join(os.path.dirname(__file__), 'pyi')
    pyiDir = None
    genAIP20Stubs(docDir, pyiOutDir=pyiDir)

    ms.uninitialize()
    # sys.exit()

def onMayaDroppedPythonFile(obj):
    if os.path.exists(docsConfig.Paths.MAYA_API):
        genAIP20Stubs(docsConfig.Paths.MAYA_API, docsConfig.Paths.PYI_DIR)
