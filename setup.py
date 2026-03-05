from setuptools import setup, find_packages
import os
import re

def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

def read_version():
    init_path = os.path.join(os.path.dirname(__file__), 'ccc', '__init__.py')
    content = open(init_path).read()
    match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if not match:
        raise RuntimeError("Unable to find __version__ in ccc/__init__.py")
    return match.group(1)

setup(
    name='ccc-tools',
    version=read_version(),
    description='Utility tools for Conda Compute Cluster',
    long_description=read('README.md'),
    author='Domen Tabernik',
    author_email='domen.tabernik@fri.uni-lj.si',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['psutil'],
    entry_points={ 'console_scripts': ['ccc = ccc.__main__:main']},
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
