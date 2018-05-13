from setuptools import setup


__version__ = '0.1.0'

setup(
    name='conff',
    py_modules=['conff'],
    version=__version__,
    description='Simple config parser with evaluator library.',
    long_description=open('README.md', 'r').read(),
    author='Robertus Johansyah',
    author_email='kororola@gmail.com',
    url='https://github.com/kororo/conff',
    download_url='https://github.com/kororo/conff/tarball/' + __version__,
    keywords=['config', 'parser', 'expression', 'parse', 'eval'],
    test_suite='conff.test',
    use_2to3=True,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
    ],
)
