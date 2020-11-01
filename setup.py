import setuptools
setuptools.setup(
    name='dawtool',
    install_requires=['pytest', 'hexdump', 'scipy'],
    entry_points={
        "console_scripts": ['dawtool=dawtool.__main__:main']
    }
)
