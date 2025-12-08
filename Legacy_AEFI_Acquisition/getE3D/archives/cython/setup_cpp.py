from distutils.core import setup, Extension
from distutils.command.build_ext import build_ext
import sys
import os

class BuildExtCommand(build_ext):
    def build_extensions(self):
        # Options de compilation optimisées
        if self.compiler.compiler_type == 'msvc':
            for ext in self.extensions:
                ext.extra_compile_args = ['/O2', '/std:c++17']
        else:
            for ext in self.extensions:
                ext.extra_compile_args = ['-O3', '-std=c++17']
        
        build_ext.build_extensions(self)

# Extension C++
cpp_module = Extension(
    'ultra_serial_cpp_module',
    sources=['ultra_serial_cpp_wrapper.cpp'],
    libraries=['kernel32'],  # Pour les API Windows
    language='c++'
)

if __name__ == "__main__":
    setup(
        name='UltraSerialCpp',
        version='1.0',
        description='Module C++ ultra-rapide pour communication série',
        ext_modules=[cpp_module],
        cmdclass={'build_ext': BuildExtCommand},
    ) 