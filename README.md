# Maya Stubgen from docs
## 模块
- ✅ maya.cmds
- ✅ maya.mel
- ✅ maya.API 1.0
- ✅ maya.API 2.0
- ✅ maya.standalone
- ✅ ufe
- ✅ pxr(Usd)
- ✅ PySide2

## 动机
我一直使用[maya-stubs](https://pypi.org/project/maya-stubs/)和mypy.stubgen创建出来的Usd stubs，来得到VS Code的代码自动完成。它们并不能满足我，所以自己来搞，大概花了一个多月的休息时间吧。

## 代码编辑器支持
我只用VS Code，所以只在上面测试过，文档风格也是VS Code支持的，我没有兴趣去支持我不使用的代码编辑器

## 使用方法
### 提供文档路径
编辑`docsConfig.py`提供本地文档路径。
#### Usd doc
Usd的文档需要从源代码构建，下载并构建:https://github.com/PixarAnimationStudios/OpenUSD/releases
```
> python USD/build_scripts/build_usd.py --docs E:/USD_WITH_DOC
```
然后把`E:/USD_WITH_DOC/docs/doxy_xml`放到`docsConfig.py`里

### 生成 stubs
你可以直接把`genAllStubs.py`扔到Maya的主界面里，也可以通过代码来调用`genAllStubs.main()`

大部分模块都有Standalone下运行的函数，如：`usd_stubgen.genFromStandalone()`。你也可以通过 maya.standalone 去生成，区别在于有部分Maya UI相关的cmds命令在standalone模式下不存在

## VS Code环境设置
`addMayaModulePathToVSCode.py`是用来快速设置环境的，你也可以手动设置