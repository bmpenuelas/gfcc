from setuptools import setup, find_packages

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='gfcc',
    version='0.3',
    description='A layer of automation for ClearCase with a touch of git flavour',
    long_description=readme(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
    keywords='git clearcase cleartool',
    url='https://github.com/bmpenuelas/gfcc',
    author='Borja Penuelas',
    author_email='bmpenuelas@gmail.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
    ],
    scripts=[
    ],
    entry_points={
        'console_scripts': [
            'gfcc=gfcc.gfcc:main',
        ]
    }
)
