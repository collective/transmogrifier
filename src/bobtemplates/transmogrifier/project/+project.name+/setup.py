from setuptools import setup, find_packages

setup(
    name='blueprints',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    install_requires = [
        'setuptools',
        'transmogrifier',
        'z3c.autoinclude',
        'venusianconfiguration',
        # custom blueprint requirements:
        'fake-factory'
    ],
    entry_points="""
    # -*- Entry points: -*-
    [z3c.autoinclude.plugin]
    target = transmogrifier
    """
)
