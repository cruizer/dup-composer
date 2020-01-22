import pathlib
from setuptools import setup

PARENT_DIR = pathlib.Path(__file__).parent
README_TEXT = (PARENT_DIR / 'README.md').read_text()

setup(
    name='dup-composer',
    version='0.1.1',
    description='Dup-composer is a front-end script for Duplicity, that lets you define your backups in a configuration file and execute them in a simple way.',
    long_description=README_TEXT,
    long_description_content_type='text/markdown',
    url='https://github.com/cruizer/dup-composer',
    author='Tamas Kalman',
    author_email='hello@tamaskalman.com',
    license='MIT',
    classifiers=[ 'Development Status :: 3 - Alpha',
                  'Environment :: Console',
                  'Operating System :: POSIX :: Linux',
                  'Programming Language :: Python :: 3.7',
                  'Topic :: System :: Archiving :: Backup'],
    packages=['dupcomposer'],
    include_package_data=False,
    install_requires=['keyring>=19.2.0', 'SecretStorage>=3.1.1',
                      'PyYAML>=5.1', 'duplicity>=0.7'],
    entry_points={'console_scripts': ['dupcomp=dupcomposer.__init__.main']}
)
