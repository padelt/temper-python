from setuptools import setup

setup(
    name='Temper',
    version='1.1.1',
    description='Reads temperature from TEMPerV1 devices (USB 0c45:7401)',
    packages=['temper'],
    install_requires=['pyusb'],
    entry_points={
        'console_scripts': [
            'temper-poll = temper.cli:main',
            'temper-snmp = temper.snmp:main'
        ]
    }
)
