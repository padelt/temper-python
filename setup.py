from setuptools import setup

setup(
    name='temperusb',
    author='Philipp Adelt',
    author_email='autosort-github@philipp.adelt.net ',
    url='https://github.com/padelt/temper-python',
    version='1.5.1',
    description='Reads temperature from TEMPerV1 devices (USB 0c45:7401)',
    long_description=open('README.md').read(),
    packages=['temperusb'],
    install_requires=[
        'pyusb>=1.0.0rc1',
    ],
    entry_points={
        'console_scripts': [
            'temper-poll = temperusb.cli:main',
            'temper-snmp = temperusb.snmp:main'
        ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
)
