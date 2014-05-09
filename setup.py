from setuptools import setup
import glob

setup(name='BYONDTools',
    version='0.0.1',
    description='Tools and interfaces for interacting with the BYOND game engine.',
    url='http://github.com/N3X15/BYONDTools',
    author='N3X15',
    author_email='nexisentertainment@gmail.com',
    license='MIT',
    packages=['byond'],
    install_requires=[
        'Pillow'
    ],
    test_suite='tests',
    scripts=glob.glob("scripts/*.py"),
    zip_safe=False)