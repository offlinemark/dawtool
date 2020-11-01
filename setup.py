import setuptools
setuptools.setup(
    name='dawtool',
    version='0.0.1',
    author='Mark Mossberg',
    install_requires=['pytest', 'hexdump', 'scipy'],
    entry_points={
        "console_scripts": ['dawtool=dawtool.__main__:main']
    }
)
