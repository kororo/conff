import os

from setuptools import setup


def get_requirements(r: str):
    try:  # for pip >= 10
        from pip._internal.req import parse_requirements
    except ImportError:  # for pip <= 9.0.3
        from pip.req import parse_requirements

    # parse_requirements() returns generator of pip.req.InstallRequirement objects
    if os.path.exists(r):
        install_reqs = parse_requirements(r, session=pkg)
        return install_reqs
    return []


__version__ = '0.4.1'
pkg = 'conff'
rs = [str(ir.req) for ir in get_requirements('requirements.txt')]

setup(
    name=pkg,
    packages=[pkg],
    include_package_data=True,
    version=__version__,
    description='Simple config parser with evaluator library.',
    long_description=open('README.rst', 'r').read(),
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
    ],
    python_requires='>=3.5',
    install_requires=rs
)
