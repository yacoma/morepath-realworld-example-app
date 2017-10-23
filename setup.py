# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

name = 'conduit-morepath'
description = (
    'Morepath Conduit implementation'
)
version = '0.0.1'


setup(
    name=name,
    version=version,
    description=description,
    author='Henri Hulski',
    author_email='henri.hulski@gazeta.pl',
    license='MIT',
    url="https://github.com/henri-hulski/realworld-starter-kit",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[
        'more.cerberus',
        'more.jwtauth',
        'more.pony',
        'argon2_cffi',
        'gunicorn',
        'pyyaml',
        'awesome-slugify'
    ],
    extras_require=dict(
        test=[
            'pytest >= 2.9.1',
            'pytest-remove-stale-bytecode',
            'pytest-env',
            'WebTest >= 2.0.14',
        ],
        pep8=[
            'flake8',
            'pep8-naming',
        ],
        coverage=[
            'pytest-cov',
        ],
        production=[
            'psycopg2',
        ]
    ),
    entry_points=dict(
        morepath=[
            'scan = conduit',
        ],
    ),
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
