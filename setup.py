from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pyDoujinshiInfo',
    version='0.1',
    author='layolu layole',
    author_email='layolulayole@gmail.com',
    url='https://github.com/layolu/pyDoujinshiInfo',
    description='API wrapper for doujinshi.info',
    install_requires=requirements,
    license='Apache 2.0'
)