# -*- coding: utf-8 -*-

# 作者：石池

from __future__ import annotations

import os

import mypy.stubgen
import mypy.moduleinspect



class ModuleInspect(object):

    def get_package_properties(self, package_id: str) -> mypy.moduleinspect.ModuleProperties:
        return mypy.moduleinspect.get_package_properties(package_id)

    def __enter__(self) -> ModuleInspect:
        return self

    def __exit__(self, *args: object) -> None:
        pass




mypy.stubgen.ModuleInspect = ModuleInspect



pyi_dir = os.path.join(os.path.dirname(__file__), 'pyi')
doc_dir = os.path.join(pyi_dir, 'doc')
options = [
    '-o', pyi_dir,
    '-m', 'maya.standalone',
    '--doc-dir', doc_dir
]

mypy.stubgen.main(options)
