"""
Flask Principal
---------------

Identity management for Flask.

Links
`````

* `documentation <http://packages.python.org/Flask-Principal/>`_
* `source <https://github.com/mattupstate/flask-principal>`_
* `development version
  <https://github.com/mattupstate/flask-principal/raw/develop#egg=Flask-Principal-dev>`_

"""

from setuptools import setup


setup(
    name='Flask-Principal',
    version='0.3.3',
    url='http://packages.python.org/Flask-Principal/',
    license='MIT',
    author='Ali Afshar',
    author_email='aafshar@gmail.com',
    maintainer='Matt Wright',
    maintainer_email='matt@nobien.net',
    description='Identity management for flask',
    long_description=__doc__,
    packages=['flask_principal'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask', 'blinker'
    ],
    test_suite='nose.collector',
    tests_require=[
        'pytest', 'nose'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
