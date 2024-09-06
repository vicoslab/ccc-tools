from setuptools import setup, find_packages
import os

def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

setup(
    name='ccc-tools',
    version='0.3.2',
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
