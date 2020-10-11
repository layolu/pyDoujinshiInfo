from setuptools import setup

with open('requirements.txt') as fr:
    requirements = fr.read().splitlines()

with open('README.md') as fl:
    long_description = fl.read()

setup(
    name='pyDoujinshiInfo',
    packages=['pyDoujinshiInfo'],
    version='0.1.0.5',
    author='layolu layole',
    author_email='layolulayole@gmail.com',
    url='https://github.com/layolu/pyDoujinshiInfo',
    description='Unofficial API wrapper for doujinshi.info',
    long_description=long_description,
    long_description_content_type='text/markdown',
    keywords='doujinshi, api-wrapper, rest-api-wrapper, python3',
    install_requires=requirements,
    license='Apache 2.0'
)
