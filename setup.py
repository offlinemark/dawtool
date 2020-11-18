import setuptools
setuptools.setup(
    name='dawtool',
    version='0.0.1',
    author='Mark Mossberg',
    python_requires='>=3.7',
    install_requires=['pytest', 'hexdump', 'scipy'],
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": ['dawtool=dawtool.__main__:main']
    }
)
