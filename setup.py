from setuptools import setup, find_packages

setup(
    name='transmogrifier',
    version='2.0.0',
    description='A configurable pipeline, aimed at transforming content for '
                'import and export',
    long_description=(open('README.rst').read() + '\n' +
                      open('CHANGES.rst').read()),
    # Get more strings from
    # http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Programming Language :: Python',
    ],
    keywords='',
    author='Asko Soukka',
    author_email='asko.soukka@iki.fi',
    url='https://github.com/datakurre/transmogrifier/',
    license='GPL',
    packages=find_packages('src', exclude=['ez_setup']),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'six',
        'future',
        'docopt',
        'chameleon',
        'zope.interface',
        'zope.component',
        'zope.configuration',
    ],
    extras_require={'path': ['z3c.pt'],
                    'test': ['zope.testing']},
    entry_points={
        'console_scripts': [
            'transmogrify=transmogrifier:__main__'
        ]
    }
)
