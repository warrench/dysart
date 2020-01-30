from setuptools import setup, find_packages

setup(
    name='Dysart',
    version='0.1dev',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.16',
        'matplotlib>=3.1',
        'pint>=0.9',
        'lmfit>=0.9.13',
        'mongoengine>=0.18.2',
        'uncertainties>=3.1',
        'msgpack>=0.5'
        'h5py>=2.10.0'
        'Labber'
    ],
    long_description=open('README.md').read(),
    url='https://github.com/qmit/dysart'
)
