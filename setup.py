"""
Flask Principal
---------------

Identity management for Flask.

Links
`````

* `documentation <http://packages.python.org/Flask-Principal/>`_
* `source <http://bitbucket.org/aafshar/flask-principal-main>`_

"""
from setuptools import setup


setup(
    name='Flask-Principal',
    version='0.1',
    url='http://packages.python.org/Flask-Principal/',
    license='MIT',
    author='Ali Afshar',
    author_email='aafshar@gmail.com',
    description='Identity management for flask',
    long_description=__doc__,
    packages=['flaskext'],
    namespace_packages=['flaskext'],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask', 'blinker'
    ],
    tests_require=[
        'py', 
    ],
    test_suite='nose.collector',
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
