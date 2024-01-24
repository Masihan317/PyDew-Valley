from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but some modules need help.
buildOptions = dict(
    packages = [],  # List any additional packages to include
    excludes = [],  # List packages to exclude
    include_files = ['audio/', 'data/', 'graphics/', 'font/', 'code/']  # List of folders to include
)

executables = [
    Executable('code/main.py', base=None)  # 'base=None' is used for non-Windows systems
]

setup(
    name='Pydew Valley',
    version='1.0',
    description='A cute farming game inspired by Stardew Valley.',
    options=dict(build_exe=buildOptions),
    executables=executables
)