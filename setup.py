from setuptools import setup

setup(
    name='temperusb',
    author='Philipp Adelt',
    author_email='info@philipp.adelt.net ',
    url='https://github.com/padelt/temper-python',
    version='1.1.1',
    description='Reads temperature from TEMPerV1 devices (USB 0c45:7401)',
    long_description=open('README.md').read(),
    packages=['temperusb'],
    install_requires=['pyusb'],
    entry_points={
        'console_scripts': [
            'temper-poll = temper.cli:main',
            'temper-snmp = temper.snmp:main'
        ]
    }
)
