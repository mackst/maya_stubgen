# -*- coding: utf-8 -*-

# 作者：石池

from html.parser import HTMLParser
import keyword
import inspect
import io
import os.path
from pprint import pformat
import re
import typing
import sys

import docsConfig


class CmdParaser(HTMLParser):

    def __init__(self):
        super(CmdParaser, self).__init__()
        self._returnValueCount = 0
        self._dataReadCount = 0
        self.returnType = []
        self.returnValueHit = False

        self.synopsis = ''
        self._synopsisHit = False

        self.cmdDoc = ''
        self.__cmdDocStop = False
        self._codeStart = False

        self.cmdArguments = {}
        self.__argumentStart = False
        self.__currentArgs = []
        self.__appendArg = False
        self.__currentArgDoc = ''
        self.__redCurrentArgDoc = False
        self.__redCurrentArgDocEnd = False
        self.__addToArguments = False

        self.codeExample = ''
        self.__codeExampleHite = False
        self.__codeExampleStart = False

    def handle_starttag(self, tag, attrs):
        if tag == 'p' and ('id', 'synopsis') in attrs:
            self._synopsisHit = True

        if tag == 'a' and ('name', 'hReturn') in attrs:
            self.returnValueHit = True

        if tag == 'a' and ('name', 'hFlags') in attrs:
            self.__cmdDocStop = True
            self.__argumentStart = True

        if tag == 'code' and self.__argumentStart:
            self.__appendArg = True
            self.__addToArguments = False

        if tag == 'td' and self.__argumentStart and self.__appendArg and not attrs:
            self.__appendArg = False
            self.__redCurrentArgDoc = True

        if tag == 'a' and ('name', 'hExamples') in attrs:
            self.__argumentStart = False
            self.__codeExampleHite = True
        
        if tag == 'pre' and self.__codeExampleHite:
            self.__codeExampleStart = True

    def handle_endtag(self, tag):
        if self._codeStart and tag == 'code':
            self._codeStart = False
        
        if self._synopsisHit and tag == 'code':
            self._synopsisHit = False

        if self.__redCurrentArgDoc and tag == 'td':
            self.__redCurrentArgDoc = False
            self.__addToArguments = True

    def handle_data(self, data):
        if (self.synopsis and not self._synopsisHit) and not self.__cmdDocStop:
            self.cmdDoc += data

        if self._synopsisHit:
            self.synopsis += data
            # self.synopsis = self.synopsis.replace('\n', '')

        numReturnType = len(self.returnType)
        if self.returnValueHit and numReturnType < 3:
            self.returnType.append(data)

        if self.__appendArg and self.__argumentStart:
            if data.strip():
                self.__currentArgs.append(data)
        
        if self.__redCurrentArgDoc and self.__argumentStart:
            self.__currentArgDoc += data

        if self.__addToArguments and self.__argumentStart:
            self.__redCurrentArgDoc = False

            arg = ''.join(self.__currentArgs)
            if arg:
                self.cmdArguments[arg] = self.__currentArgDoc#.strip()
            self.__currentArgs = []
            self.__currentArgDoc = ''

        if self.__codeExampleStart:
            self.codeExample += data


def getFuncSynopsisTypes(synopsis: str):
    types = {}
    ftypes = synopsis.split('(')[1]
    ftypes = ftypes.split(')')[0]
    ftypes = ftypes.split(', [')
    for t in ftypes:
        x = t.strip()#.replace('[', '').replace(']', '')
        if '=' in x:
            name, t_ = x.split('=')
            types[t_[:-1]] = None

            # if t_ == 'linear':
            #     print(synopsis)

    return types


helpFuncTypes = {'(multi-use)': 'typing.Any',
 'Angle': float.__name__,
 'Angle (Query Arg Mandatory)': float.__name__,
 'Angle Angle': 'tuple[float, float]',
 'Angle Angle Angle': 'tuple[float, float, float]',
 'Float': float.__name__,
 'Float (Query Arg Mandatory)': float.__name__,
 'Float (multi-use)': float.__name__,
 'Float Float': 'tuple[float, float]',
 'Float Float (multi-use)': 'tuple[float, float]',
 'Float Float Float': 'tuple[float, float, float]',
 'Float Float Float (multi-use)': 'tuple[float, float, float]',
 'Float Float Float Float': 'tuple[float, float, float, float]',
 'Float Float Float Float Float Float': 'tuple[float, float, float, float, float, float]',
 'Float Float Float Float Float Float (multi-use)': 'tuple[float, float, float, float, float, float]',
 'Float Float Float Float Float Float Float Float Float Float Float Float Float Float Float Float': 'tuple[float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]',
 'Float Int String (Query Arg Mandatory)': 'tuple[float, int, str]',
 'Float Int String (Query Arg Optional)': 'tuple[float, int, str]',
 'Float Int String (multi-use)': 'tuple[float, int, str]',
 'Float String': 'tuple[float, str]',
 'Float on|off (multi-use)': 'tuple[float, bool]',
 'FloatRange (Query Arg Mandatory)': 'list[float]',
 'FloatRange (multi-use)': 'list[float]',
 'FloatRange (multi-use) (Query Arg Mandatory)': 'list[float]',
 'IndexRange (Query Arg Mandatory)': 'list[int]',
 'IndexRange (multi-use)': 'list[int]',
 'IndexRange (multi-use) (Query Arg Mandatory)': 'list[int]',
 'Int': int.__name__,
 'Int (Query Arg Mandatory)': int.__name__,
 'Int (Query Arg Optional)': int.__name__,
 'Int (multi-use)': int.__name__,
 'Int Float': 'tuple[int, float]',
 'Int Float (multi-use)': 'tuple[int, float]',
 'Int Float Float': 'tuple[int, float, float]',
 'Int Float Float Float': 'tuple[int, float, float, float]',
 'Int Float Float Float (multi-use)': 'tuple[int, float, float, float]',
 'Int Float [ Float Float ] (multi-use)': 'tuple[int, float, tuple[float, float]]',
 'Int Int': 'tuple[int, int]',
 'Int Int (Query Arg Mandatory)': 'tuple[int, int]',
 'Int Int (multi-use)': 'tuple[int, int]',
 'Int Int (multi-use) (Query Arg Mandatory)': 'tuple[int, int]',
 'Int Int Float': 'tuple[int, int, float]',
 'Int Int Float Float Float': 'tuple[int, int, float, float, float]',
 'Int Int Int': 'tuple[int, int, int]',
 'Int Int Int (multi-use)': 'tuple[int, int, int]',
 'Int Int Int Int': 'tuple[int, int, int, int]',
 'Int Int Int Int Int': 'tuple[int, int, int, int, int]',
 'Int Int Int Int Int Int': 'tuple[int, int, int, int, int, int]',
 'Int Name': 'tuple[int, str]',
 'Int Script (multi-use)': 'tuple[int, str]',
 'Int String': 'tuple[int, str]',
 'Int String (multi-use)': 'tuple[int, str]',
 'Int String Int (multi-use)': 'tuple[int, str]',
 'Int [ Int ]': 'tuple[int, list[int]]',
 'Int [ String ]': 'tuple[int, list[str]]',
 'Int on|off': 'tuple[int, bool]',
 'Int on|off (multi-use)': 'tuple[int, bool]',
 'Int on|off String String String String': 'tuple[int, bool, str, str, str, str]',
 'Int64': int.__name__,
 'Int64 (Query Arg Mandatory)': int.__name__,
 'Int64 (multi-use)': int.__name__,
 'Int[...]': 'list[int]',
 'Length': float.__name__,
 'Length (Query Arg Mandatory)': float.__name__,
 'Length (multi-use)': float.__name__,
 'Length Length': 'tuple[float, float]',
 'Length Length Length': 'tuple[float, float, float]',
 'Length Length Length (multi-use)': 'tuple[float, float, float]',
 'Length Length Length Float (multi-use)': 'tuple[float, float, float, float]',
 'Length Length Length Length': 'tuple[float, float, float, float]',
 'Length Length Length Length (multi-use)': 'tuple[float, float, float, float]',
 'Length Length Length Length Length': 'tuple[float, float, float, float, float]',
 'Name': str.__name__,
 'Name (Query Arg Mandatory)': str.__name__,
 'Name (multi-use)': str.__name__,
 'Name Int': 'tuple[str, int]',
 'Name String': 'tuple[str, str]',
 'Name on|off': 'tuple[str, bool]',
 'Script': str.__name__,
 'Script Script': 'tuple[str, str]',
 'Script String': 'tuple[str, str]',
 'String': str.__name__,
 'String (Query Arg Mandatory)': str.__name__,
 'String (Query Arg Optional)': str.__name__,
 'String (multi-use)': str.__name__,
 'String (multi-use) (Query Arg Mandatory)': str.__name__,
 'String (multi-use) (Query Arg Optional)': str.__name__,
 'String Float': 'tuple[str, float]',
 'String Float (multi-use)': 'tuple[str, float]',
 'String Float (multi-use) (Query Arg Optional)': 'tuple[str, float]',
 'String Float Float': 'tuple[str, float, float]',
 'String Float Float (multi-use)': 'tuple[str, float, float]',
 'String Float Float Float': 'tuple[str, float, float, float]',
 'String Float Float Float (multi-use)': 'tuple[str, float, float, float]',
 'String Float Float Float Float (multi-use)': 'tuple[str, float, float, float, float]',
 'String Int': 'tuple[str, int]',
 'String Int (multi-use)': 'tuple[str, int]',
 'String Int (multi-use) (Query Arg Optional)': 'tuple[str, int]',
 'String Int Float': 'tuple[str, int, float]',
 'String Int Float Float Float (multi-use)': 'tuple[str, int, float, float, float]',
 'String Int Int': 'tuple[str, int, int]',
 'String Int Int (multi-use)': 'tuple[str, int, int]',
 'String Int Int Int': 'tuple[str, int, int, int]',
 'String Int Int Int (multi-use)': 'tuple[str, int, int, int]',
 'String Int Int Int Int (multi-use)': 'tuple[str, int, int, int, int]',
 'String Int String (multi-use)': 'tuple[str, int, str]',
 'String Int String (multi-use) (Query Arg Mandatory)': 'tuple[str, int, str]',
 'String Int on|off (multi-use)': 'tuple[str, int, bool]',
 'String Script': 'tuple[str, str]',
 'String String': 'tuple[str, str]',
 'String String (Query Arg Mandatory)': 'tuple[str, str]',
 'String String (Query Arg Optional)': 'tuple[str, str]',
 'String String (multi-use)': 'tuple[str, str]',
 'String String Float': 'tuple[str, str, float]',
 'String String Int': 'tuple[str, str, int]',
 'String String Int (multi-use)': 'tuple[str, str, int]',
 'String String Int Int (multi-use)': 'tuple[str, str, int, int]',
 'String String Int String (multi-use)': 'tuple[str, str, int, str]',
 'String String Script (multi-use)': 'tuple[str, str, str]',
 'String String String': 'tuple[str, str, str]',
 'String String String (multi-use)': 'tuple[str, str, str]',
 'String String String String': 'tuple[str, str, str, str]',
 'String String String String (multi-use)': 'tuple[str, str, str, str]',
 'String String String String String': 'tuple[str, str, str, str, str]',
 'String String String String String String': 'tuple[str, str, str, str, str, str]',
 'String String String on|off': 'tuple[str, str, str, bool]',
 'String String UnsignedInt': 'tuple[str, str, int]',
 'String String on|off': 'tuple[str, str, bool]',
 'String String[...] (Query Arg Mandatory)': 'tuple[str, list[str]]',
 'String UnsignedInt': 'tuple[str, int]',
 'String UnsignedInt String Float (multi-use)': 'tuple[str, int, str, float]',
 'String [ String String ]': 'tuple[str, tuple[str, str]]',
 'String [ String ]': 'tuple[str, list[str]]',
 'String on|off': 'tuple[str, bool]',
 'String on|off (multi-use)': 'tuple[str, bool]',
 'String on|off (multi-use) (Query Arg Mandatory)': 'tuple[str, bool]',
 'String[...]': 'list[str]',
 'String[...] (Query Arg Mandatory)': 'list[str]',
 'Time': float.__name__,
 'Time (multi-use)': float.__name__,
 'Time (multi-use) (Query Arg Mandatory)': float.__name__,
 'Time Time Float': 'tuple[float, float, float]',
 'TimeRange': 'list[float]',
 'TimeRange (Query Arg Mandatory)': 'list[float]',
 'TimeRange (multi-use)': 'list[float]',
 'TimeRange (multi-use) (Query Arg Mandatory)': 'list[float]',
 'TimeRange on|off': 'tuple[list[float], bool]',
 'UnsignedInt': int.__name__,
 'UnsignedInt (Query Arg Mandatory)': int.__name__,
 'UnsignedInt (Query Arg Optional)': int.__name__,
 'UnsignedInt (multi-use)': int.__name__,
 'UnsignedInt (multi-use) (Query Arg Mandatory)': int.__name__,
 'UnsignedInt Float (multi-use)': 'tuple[int, float]',
 'UnsignedInt Float Float String': 'tuple[int, float, float, str]',
 'UnsignedInt Float Float String Float': 'tuple[int, float, float, str, float]',
 'UnsignedInt Length (multi-use)': 'tuple[int, float]',
 'UnsignedInt String': 'tuple[int, str]',
 'UnsignedInt String (multi-use)': 'tuple[int, str]',
 'UnsignedInt String Float': 'tuple[int, str, float]',
 'UnsignedInt String Float Float Float': 'tuple[int, str, float, float, float]',
 'UnsignedInt String Float Float Float Float': 'tuple[int, str, float, float, float, float]',
 'UnsignedInt String Int': 'tuple[int, str, int]',
 'UnsignedInt String String': 'tuple[int, str, str]',
 'UnsignedInt String String (multi-use)': 'tuple[int, str, str]',
 'UnsignedInt String UnsignedInt UnsignedInt': 'tuple[int, str, int, int]',
 'UnsignedInt String on|off': 'tuple[int, str, bool]',
 'UnsignedInt UnsignedInt': 'tuple[int, int]',
 'UnsignedInt UnsignedInt (Query Arg Optional)': 'tuple[int, int]',
 'UnsignedInt UnsignedInt (multi-use)': 'tuple[int, int]',
 'UnsignedInt UnsignedInt Float String': 'tuple[int, int, float, float]',
 'UnsignedInt UnsignedInt UnsignedInt': 'tuple[int, int, int]',
 'UnsignedInt UnsignedInt UnsignedInt Float Float (multi-use)': 'tuple[int, int, int, float, float]',
 'UnsignedInt UnsignedInt UnsignedInt UnsignedInt': 'tuple[int, int, int, int]',
 'UnsignedInt UnsignedInt UnsignedInt UnsignedInt on|off': 'tuple[int, int, int, int, bool]',
 'UnsignedInt on|off': 'tuple[int, bool]',
 'UnsignedInt on|off (multi-use)': 'tuple[int, bool]',
 '[ Float Float Float ] (multi-use)': tuple[float, float, float],
 '[ String Script ]': 'tuple[str, str]',
 '[ on|off Float ]': 'tuple[bool, float]',
 'on|off': bool.__name__,
 'on|off (Query Arg Mandatory)': bool.__name__,
 'on|off (Query Arg Optional)': bool.__name__,
 'on|off (multi-use)': bool.__name__,
 'on|off String': 'tuple[bool, str]',
 'on|off String Int': 'tuple[bool, str, int]',
 'on|off String String String String (multi-use)': 'tuple[bool, str, str, str, str]',
 'on|off on|off': 'tuple[bool, bool]',
 'on|off on|off on|off': 'tuple[bool, bool, bool]',
 'on|off on|off on|off on|off': 'tuple[bool, bool, bool, bool]',
 'on|off on|off on|off on|off on|off': 'tuple[bool, bool, bool, bool, bool]',
 'on|off on|off on|off on|off on|off on|off on|off': 'tuple[bool, bool, bool, bool, bool, bool, bool]'}

cmdSynopsisTypes = {
    'float': float.__name__, 
    'string': str.__name__, 
    'boolean': bool.__name__, 
    'name': str.__name__, 
    'linear': float.__name__, 
    'angle': float.__name__, 
    'int': int.__name__, 
    'floatrange': '[float]', 
    'uint': int.__name__, 
    'time': float.__name__, 
    # '': None, 
    'timerange': '[float]', 
    'script': str.__name__, 
    'int64': int.__name__
}


cmdArgumentTypes = {
    'float': 'f_: float', 
    'float float': 'f_: float, f1_: float', 
    'string': 'string_: str', 
    'boolean': 'boolean_: bool', 
    'name': 'name_: str', 
    'linear': 'linear_: float', 
    'angle': 'angle_: float', 
    'int': 'int1_: int', 
    'floatrange': 'floatrange_: list[float]', 
    'uint': 'uint_: int', 
    'time': 'time_: float', 
    # '': 'None', 
    'timerange': 'timerange_: list[float]', 
    'script': 'script_: str', 
    'int64': 'int64_: int',

    'objects': 'objects_: typing.Optional(list[str])',
    'target object': 'target_: list[str], object_: str',
    'curve': 'curve_: str',
    'curve curve': 'curve_: str, curve1_: str',
    'curve curve curve': 'curve_: str, curve1_: str, curve2_: str',
    'curve curve curve | surface': 'curve_: str, curve1_: str, curve2_: str',
    'object': 'object_: str',
    'object object': 'object_: str, object1_: str',
    'name': 'name_: str',
    'string string': 'string_: str, string1_: str',
    'stringstring': 'string_: str, string1_: str',
    'string string string string': 'string1_: str, string2_: str, string3_: str, string4_: str',
    'selectionList': 'selectionList: list[str]',
    'camera': 'camera_: str',
    'editorName': 'editorName_: str',
    'groupName': 'groupName_: str',
    'panelName': 'panelName_: str',
    'imageName': 'imageName_: str',
    'surface': 'surface_: str',
    'surface surface': 'surface_: str, surface1_: str',
    'int': 'int1_: int',
    'targetList': 'targetList_: list[str]',
    'attribute': 'attribute_: str',
    'contextName': 'contextName_: str',
    ', float, float,': 'f1_: float, f2_: float',
    'target  object': 'target_: str, object_: str',
    'node': 'node_: str',
    'filename': 'filename_: str',
    'surfaceIsoparm surfaceIsoparm': 'surfaceIsoparm_: str, surfaceIsoparm1_: str',
    'dagObject dagObject': 'dagObject_: str, dagObject1_: str',
    'context': 'context_: str',
    'poly poly': 'poly_: str, poly1_: str',
}

cmdKeyWordTypes = {
    'float': float.__name__, 
    'string': str.__name__, 
    'boolean': bool.__name__, 
    'name': str.__name__, 
    'linear': float.__name__, 
    'angle': float.__name__, 
    'int': int.__name__, 
    'floatrange': 'list[float]', 
    'uint': int.__name__, 
    'time': float.__name__, 
    # '': None, 
    'timerange': 'list[float]', 
    'script': str.__name__, 
    'int64': int.__name__,

    '[[, boolean, float, ]]': 'list[tuple[bool, float]]',
    '[[, float, float, float, ]]': 'list[list[float]]',
    '[angle, angle, angle]': 'list[float]',
    '[angle, angle]': 'list[float]',
    '[boolean, boolean, boolean, boolean, boolean, boolean, boolean]': 'list[bool]',
    '[boolean, boolean, boolean, boolean, boolean]': 'list[bool]',
    '[boolean, boolean, boolean, boolean]': 'list[bool]',
    '[boolean, boolean, boolean]': 'list[bool]',
    '[boolean, boolean]': 'list[bool]',
    '[boolean, string, int]': 'tuple[bool, str, int]',
    '[boolean, string, string, string, string]': 'tuple[bool, str, str, str, str]',
    '[float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]': 'list[float]',
    '[float, float, float, float]': 'list[float]',
    '[float, float, float]': 'list[float]',
    '[float, float]': 'list[float]',
    '[int, boolean, string, string, string, string]': 'tuple[int, bool, str, str, str, str]',
    '[int, boolean]': 'tuple[int, bool]',
    '[int, float, [, float, float, ]]': 'tuple[int, float, list[float]]',
    '[int, float, float, float]': 'tuple[int, float, float, float]',
    '[int, float]': 'tuple[int, float]',
    '[int, int, float, float, float]': 'tuple[int, int, float, float, float]',
    '[int, int, float]': 'tuple[int, int, float]',
    '[int, int, int, int, int, int]': 'list[int]',
    '[int, int, int, int, int]': 'list[int]',
    '[int, int, int, int]': 'list[int]',
    '[int, int, int]': 'list[int]',
    '[int, int]': 'list[int]',
    '[int, name]': 'tuple[int, str]',
    '[int, script]': 'tuple[int, str]',
    '[int, string, int]': 'tuple[int, str, int]',
    '[int, string]': 'tuple[int, str]',
    '[linear, linear, linear, float]': 'list[float]',
    '[linear, linear, linear, linear, linear]': 'list[float]',
    '[linear, linear, linear, linear]': 'list[float]',
    '[linear, linear, linear]': 'list[float]',
    '[linear, linear]': 'list[float]',
    '[name, string]': 'list[str]',
    '[name, int]': 'tuple(str, int)',
    '[script, script]': 'list[str]',
    '[script, string]': 'list[str]',
    '[string, [, string, ], [, string, ]]': 'list[str, list[str], list[str]]',
    '[string, boolean]': 'tuple[str, bool]',
    '[string, float, float, float, float]': 'tuple[str, float, float, float, float]',
    '[string, float, float, float]': 'tuple[str, float, float, float]',
    '[string, float, float]': 'tuple[str, float, float]',
    '[string, float]': 'tuple[str, float]',
    '[string, int, boolean]': 'tuple[str, int, bool]',
    '[string, int, float, float, float]': 'tuple[str, int, float, float, float]',
    '[string, int, int, int, int]': 'tuple[str, int, int, int, int]',
    '[string, int, int, int]': 'tuple[string, int, int, int]',
    '[string, int, int]': 'tuple[str, int, int]',
    '[string, int, string]': 'tuple[str, int, str]',
    '[string, int]': 'tuple[str, int]',
    '[string, script]': 'list[str]',
    '[string, string, boolean]': 'tuple[str, str, bool]',
    '[string, string, int, int]': 'tuple[str, str, int, int]',
    '[string, string, int, string]': 'tuple[str, str, int, str]',
    '[string, string, int]': 'tuple[str, str, int]',
    '[string, string, script]': 'list[str]',
    '[string, string, string, string, string, string]': 'list[str]',
    '[string, string, string, string, string]': 'list[str]',
    '[string, string, string, string]': 'list[str]',
    '[string, string, string]': 'list[str]',
    '[string, string, uint]': 'tuple[str, str, int]',
    '[string, string[]]': 'tuple[str, list[str]]',
    '[string, string]': 'list[str]',
    '[string, uint, boolean]': 'tuple[str, int, bool]',
    '[string, uint, string, float]': 'tuple[str, int, str, float]',
    '[string, uint, uint, uint, uint]': 'tuple[str, int, int, int, int]',
    '[string, uint]': 'tuple[str, int]',
    '[time, time, float]': 'list[float]',
    '[time, time, time, time]': 'list[float]',
    '[timerange, boolean]': 'tuple[list[float], bool]',
    '[uint, boolean]': 'tuple[int, bool]',
    '[uint, float]': 'tuple[int, float]',
    '[uint, linear]': 'tuple[int, float]',
    '[uint, string]': 'tuple[int, str]',
    '[uint, uint, uint, float, float]': 'tuple[int, int, int, float, float]',
    '[uint, uint, uint, uint]': 'list[int]',
    '[uint, uint, uint]': 'list[int]',
    '[uint, uint]': 'list[int]',
    'int[]': 'list[int]',
    'string[]': 'list[str]'
}

cmdRetrunTypes = {
    'string[]': 'list[str]', 
    'string': str.__name__, 
    'None': 'None', 
    'boolean': bool.__name__, 
    'float[3]': 'list[float, float, float]', 
    'int': int.__name__, 
    'Any': 'typing.Any', 
    'float[]': 'list[float]', 
    'float': float.__name__, 
    'Int': int.__name__, 
    'double[]': 'list[float]', 
    'Boolean': bool.__name__, 
    'time': int.__name__, 
    'STRING': str.__name__, 
    'int[]': 'list[int]', 
    'boolean[]': 'list[bool]', 
    'selectionItem[]': 'list[str]', 
    'string[]|string|int': 'typing.Union([str], str, int)',
}

def getCmdFlagSplit(flag: str) -> tuple[str, str, typing.Optional[str]]:
    m = re.search('\)\d+\.?\d', flag)
    if m:
        v = m.group()[1:]
        # try:
        name, type_ = flag.split(v)
        # except Exception as error:
        #     print(flag)
        #     raise
        return (name, type_, v)
    # try:
    name, type_ = flag.split(')')
    # except Exception as error:
    #     print(flag)
    #     raise
    name += ')'
    return (name, type_, None)

def getFunStr(synopsis: str, cmdKeyWords: list[str], edit=False, query=False):
    funStr = ''

    keyWords = []
    cmdFlags = {}
    for word in cmdKeyWords:
        if len(word) > 30: continue
        name, t_, v_ = getCmdFlagSplit(word)
        # try:
        lf, w_ = name.split('(')
        # except Exception as error:
        #     print(word)
        #     print(name, t_, v_)
        #     raise
        sf = w_.split(')')[0]
        cmdFlags[lf] = sf
        keyWords.append('{}: {} = ...'.format(lf, cmdKeyWordTypes[t_]))
    
    if edit:
        keyWords.append('edit: bool = ...')
    if query:
        keyWords.append('query: bool = ...')

    funcName, ftypes = synopsis.split('(')
    ftypes = ftypes.split(')')[0]
    ftypes = ftypes.split('=')[0]
    ftypes = ftypes.split(',')[:-1]
    arguments = []
    for t in ftypes:
        arg = t.strip().replace('.', '')
        if not arg:
            continue

        arg = arg.replace('\n', ' ')
        if '|' in arg:
            arg = arg.split('|')[0]
        args = arg.split(' ')
        typeCount = {}
        for a in args:
            a = a.replace('[', '').replace(']', '')
            if not a.strip(): continue
            if a in typeCount:
                typeCount[a] += 1
            else:
                typeCount[a] = 1
            
            an = a + str(typeCount[a]) + '_'
            arguments.append('{}: {}'.format(an, 'typing.Any'))

    funStr = 'def {}('.format(funcName.strip())
    if arguments:
        funStr += ', '.join(arguments) + ', '
    temp = ', '.join(keyWords)
    funStr += temp + ')'
    funStr = funStr.replace('\n', '')

    overload = funStr
    for lf in cmdFlags:
        sf = cmdFlags[lf]
        if sf:
            overload = overload.replace(lf+':', sf+':')
    
    # if edit:
    #     overload = overload.replace('edit:', 'e:')
    # if query:
    #     overload = overload.replace('query:', 'q:')

    return (funStr, overload)

def getCmdStr(synopsis: str, returnType: list[str], docContent: str, arguments: dict, example: str):
    rt = returnType[-1]
    query = 'NOT queryable' not in docContent
    edit = 'NOT editable' not in docContent
    funcStr, funcOverload = getFunStr(synopsis, list(arguments.keys()), edit, query)
    funcRt = ' -> {}:\n'.format(cmdRetrunTypes.get(rt, 'typing.Any'))
    funcStr += funcRt
    funcOverload += funcRt
    dcFirstLineIndex = docContent.find('\n')
    docCont = docContent[dcFirstLineIndex:].strip()
    docstring = "    '''{}\n\n".format(docCont.replace('\n', '\n\t').expandtabs(4))
    docstring += "    ### Args:\n\n"
    for arg in arguments:
        if len(arg) > 30: continue
        name, t_, v_ = getCmdFlagSplit(arg)
        arg_ = '`{}` `{}`'.format(name, cmdKeyWordTypes[t_])
        if v_:
            arg_ += '  <update in {}>'.format(v_)
        argDoc = arguments[arg].replace('\n', '\n\t\t').expandtabs(4)
        docstring += "        {}: {}\n".format(arg_, argDoc)
    docstring += '\n\n'
    docstring += "    ### Returns:\n\n"
    docstring += "        `{}`\n".format(cmdRetrunTypes.get(rt, 'typing.Any'))
    docstring += '\n\n'
    docstring += "    ### Examples:\n"
    docstring += "    ```python\n"
    docstring += "    "
    docstring += example.strip().replace("'''", '"""').replace('\n', '\n\t').expandtabs(4)
    docstring += "\n    ```'''\n\n"

    out = funcStr + docstring

    # overload function
    overload = '@typing.overload\n'
    overload += funcOverload
    overload += docstring

    return out + overload

def getArgumentRTs(parser: CmdParaser):
    types = {}
    for arg in parser.cmdArguments:
        if ']' not in arg:
            continue
        # print(arg)
        name, t = arg.split(')')
        t = t.replace('2024', '').replace('.1', '')
        types[t] = t
        if ']]' in t:
            print(parser.synopsis)

    return types

def getCmdFlags(cmdName: str, helpDoc: str) -> dict:
    flags = {}
    types = {}

    reader = io.StringIO(helpDoc)

    for i in reader:
        x = i.strip()
        if '-' in x:
            splits = x.split(' ')
            sf = splits[0][1:]
            flags[sf] = splits[1][1:]
            if len(splits) > 3:
                ts = ' '.join(splits[2:]).strip()
                # types[ts] = None
                types[sf] = ts

    return (flags, types)

def writePYI(cmdModule, htmlTemp: str, pyiPath: str):
    cmdpyi = 'import typing\n\n'
    cmdsMembers = inspect.getmembers(cmdModule)
    for cmd in cmdsMembers:
        funcName = cmd[0]
        if funcName.startswith('__'): continue
        try:
            helpDoc = cmds.help(funcName, so=1, lng='python')
        except Exception as error:
            cmdpyi += '\ndef {}(*args: typing.Any, **kwargs: typing.Any): pass\n'.format(funcName)
            continue

        htmlDoc = htmlTemp.format(funcName)
        if os.path.exists(htmlDoc):
            # continue
            with open(htmlDoc) as f:
                cmdparser = CmdParaser()
                cmdparser.feed(f.read())

                if not cmdparser.returnType:
                    continue

                cmdpyi += getCmdStr(cmdparser.synopsis, cmdparser.returnType, cmdparser.cmdDoc, cmdparser.cmdArguments, cmdparser.codeExample)

        else:
            flags, types = getCmdFlags(funcName, helpDoc)
            if not funcName.startswith('__'):
                lfFunc = '@typing.overload'
                sfFunc = '\ndef {}(*args: typing.Any, '.format(funcName)
                lfFunc += sfFunc
                onlySFFunc = False
                for sf in flags:
                    t_ = 'typing.Any'
                    if sf in types:
                        t_ = helpFuncTypes.get(types[sf], 'typing.Any')

                    lf = flags[sf]
                    onlySFFunc = not lf
                    if keyword.iskeyword(lf): lf += '_'
                    lfFunc += '{}: {} = ..., '.format(lf, t_)
                    if keyword.iskeyword(sf): sf += '_'
                    sfFunc += '{}: {} = ..., '.format(sf, t_)
                lfFunc += '):\n'
                lfFunc += "    '''{}'''\n\n".format(helpDoc.replace('\n', '\n\t').expandtabs(4))
                sfFunc += '):\n'
                sfFunc += "    '''{}'''\n\n".format(helpDoc.replace('\n', '\n\t').expandtabs(4))

                cmdpyi += sfFunc
                if not onlySFFunc:
                    cmdpyi += lfFunc

    with open(pyiPath, 'w') as pyi:
        pyi.write('{}'.format(cmdpyi))

    print('{} done.'.format(pyiPath))

def writeMelPYI(htmlTemp: str, pyiOutDir: str = None):
    import maya.mel
    cmdpyi = 'import typing\n\n'

    pyiPath, ext = os.path.splitext(os.path.abspath(maya.mel.__file__))
    melutils = os.path.join(os.path.dirname(pyiPath), 'melutils.py')
    if os.path.exists(melutils):
        cmdpyi += 'from melutils import *\n\n'

    if pyiOutDir:
        names = maya.mel.__name__.split('.')
        names.append('__init__')
        pyiPath = os.path.join(pyiOutDir, *names)
        if not os.path.exists(os.path.dirname(pyiPath)):
            os.makedirs(os.path.dirname(pyiPath))
    pyiPath += '.pyi'

    funcName = 'eval'
    htmlDoc = htmlTemp.format(funcName)
    with open(htmlDoc) as f:
        cmdparser = CmdParaser()
        cmdparser.feed(f.read())

        # cmdpyi += getCmdStr(cmdparser.synopsis, cmdparser.returnType, cmdparser.cmdDoc, cmdparser.cmdArguments, cmdparser.codeExample)
        cmdpyi += 'def eval(mel: str) -> typing.Any:\n'
        cmdpyi += "    '''\n"
        cmdpyi += "    ```python\n"
        cmdpyi += "    "
        cmdpyi += cmdparser.codeExample.strip().replace("'''", '"""').replace('\n', '\n\t').expandtabs(4)
        cmdpyi += "\n    ```'''"

    with open(pyiPath, 'w') as pyi:
        pyi.write(cmdpyi)

    print('{} done.'.format(pyiPath))

def genCmdStubs(helpDir: str = '', pyiOutDir: str = None):
    import maya.cmds as cmds

    if not helpDir:
        return
    
    pyRefDir = os.path.join(helpDir, 'CommandsPython')
    if not os.path.exists(pyRefDir):
        return
    
    htmlTemp = pyRefDir + '\\{}.html'

    cmdPyiPath, ext = os.path.splitext(os.path.abspath(cmds.__file__))
    if pyiOutDir:
        names = cmds.__name__.split('.')
        names.append('__init__')
        cmdPyiPath = os.path.join(pyiOutDir, *names)
        if not os.path.exists(os.path.dirname(cmdPyiPath)):
            os.makedirs(os.path.dirname(cmdPyiPath))
    cmdPyiPath += '.pyi'

    writePYI(cmds, htmlTemp, cmdPyiPath)
    writeMelPYI(htmlTemp, pyiOutDir)

def genFromStandalone():
    import maya.standalone as ms

    ms.initialize('python')

    pyiDir = os.path.join(os.path.dirname(__file__), 'pyi')
    pyiDir = None

    helpDir = "E:\\coding\\docs\\maya-user-guide-2024-zh-cn"
    genCmdStubs(helpDir, pyiDir)

    ms.uninitialize()
    # sys.exit()


def onMayaDroppedPythonFile(obj):
    if os.path.exists(docsConfig.Paths.MAYA_HLEP):
        genCmdStubs(docsConfig.Paths.MAYA_HLEP, docsConfig.Paths.PYI_DIR)
