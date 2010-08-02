Flask Principal
===============

*"I am that I am"*


Introduction
------------

Flask-Principal provides a very loose framework to tie in providers of two
types of service, often located in different parts of a web application:

    1. Authentication providers
    2. User information providers

For example, an authentication provider may be oauth, using Flask-OAuth and
the user information may be stored in a relational database. Looseness of
the framework is provided by using signals as the interface.

The major components are the Identity, Needs, Permission, and the Principal.

    1. The Identity represents the user, and is stored/loaded from the cookie
       sessions.
    
    2. A need is a pair of (method, value) where method is used to specify
       common things such as `"role"`, `"user"`, etc. And the value is the
       value. An example of such is `('role', 'admin')`. Which would be a
       Need for a admin role.

    2. A permission is a set of requirements, any of which should be
       present for access to a resource.
       
    3. A Principal is the context of a certain identity against a certain Permission.


Links
-----

* `documentation <http://packages.python.org/Flask-Principal/>`_
* `source <http://bitbucket.org/aafshar/flask-principal-main>`_


Protecting access to resources
------------------------------

For users of Flask-Principal (not authentication providers), access
restriction is easy to define as both a decorator and a context manager. A
simple quickstart example is presented with commenting::

    from flask import Flask, Response
    from flaskext.principal import Permission, RoleNeed

    app = Flask(__name__)

    # Create a permission with a single Need, in this case a RoleNeed.
    admin_permission = Permission(RoleNeed('admin'))

    # protect a view with a principal for that need
    @app.route('/admin')
    @admin_permission.require()
    def do_admin_index():
        return Response('Only if you are an admin')

    # this time protect with a context manager
    @app.route('/articles')
    def do_articles():
        with admin_permission.require():
            return Response('Only if you are admin')


API
===

.. automodule:: flaskext.principal


Starting the extension
----------------------

.. autofunction:: flaskext.principal.init_principal


Main Types
----------

.. autoclass:: flaskext.principal.Permission
    :members:

.. autoclass:: flaskext.principal.Identity
    :members:

.. autoclass:: flaskext.principal.AnonymousIdentity
    :members:

.. autoclass:: flaskext.principal.Principal
    :members:

.. autofunction:: flaskext.principal.set_identity


Predefined Need Types
---------------------

.. autoclass:: flaskext.principal.Need
.. autoattribute:: flaskext.principal.RoleNeed
.. autoattribute:: flaskext.principal.UserNeed

Relevant Signals
----------------

.. autoattribute:: flaskext.principal.identity_changed
.. autoattribute:: flaskext.principal.identity_loaded


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

