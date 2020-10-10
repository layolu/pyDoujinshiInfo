from setuptools import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='pyDoujinshiInfo',
    packages=['pyDoujinshiInfo'],
    version='0.1.0',
    author='layolu layole',
    author_email='layolulayole@gmail.com',
    url='https://github.com/layolu/pyDoujinshiInfo',
    description='Unofficial API wrapper for doujinshi.info',
    keywords='doujinshi, api-wrapper, rest-api-wrapper, python3',
    install_requires=requirements,
    license='Apache 2.0'
)
