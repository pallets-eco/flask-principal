
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

The major components are the Identity, Needs, Permission, and the IdentityContext.

    1. The Identity represents the user, and is stored/loaded from various
       locations (eg session) for each request. The Identity is the user's
       avatar to the system. It contains the access rights that the user has.
    
    2. A Need is the smallest grain of access control, and represents a specific
       parameter for the situation. For example "has the admin role", "can edit
       blog posts".
    
       Needs are any tuple, or probably could be object you like, but a tuple
       fits perfectly. The predesigned Need types (for saving your typing) are
       either pairs of (method, value) where method is used to specify
       common things such as `"role"`, `"user"`, etc. And the value is the
       value. An example of such is `('role', 'admin')`. Which would be a
       Need for a admin role. Or Triples for use-cases such as "The permission
       to edit a particular instance of an object or row", which might be represented
       as the triple `('article', 'edit', 46)`, where 46 is the key/ID for that
       row/object.
       
       Essentially, how and what Needs are is very much down to the user, and is
       designed loosely so that any effect can be achieved by using custom
       instances as Needs.

       Whilst a Need is a permission to access a resource, an Identity should
       provide a set of Needs that it has access to.

    2. A Permission is a set of requirements, any of which should be
       present for access to a resource.
       
    3. An IdentityContext is the context of a certain identity against a certain
       Permission. It can be used as a context manager, or a decorator.


.. graphviz::


    digraph g {
        rankdir="LR" ;
        node [ colorscheme="pastel19" ];
        fixedsize = "true" ;
        i [label="Identity", shape="circle" style="filled" width="1.5", fillcolor="1"] ;
        p [label="Permission", shape="circle" style="filled" width="1.5" fillcolor="2"] ;
        n [label="<all> Needs|{<n1>RoleNeed|<n2>ActionNeed}", shape="Mrecord" style="filled" fillcolor="3"] ;
        c [label="IdentityContext", shape="box" style="filled,rounded" fillcolor="4"] ;
        p -> n:all ;
        c -> i ;
        c -> p ;
        i -> n:n1 ;
        i -> n:n2 ;

    }



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
    from flask_principal import Principal, Permission, RoleNeed

    app = Flask(__name__)

    # load the extension
    principals = Principal(app)

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

Authentication providers
------------------------

Authentication providers should use the `identity-changed` signal to indicate
that a request has been authenticated. For example::


    from flask import current_app
    from flask_principal import Identity, identity_changed

    def login_view(req):
        username = req.form.get('username')
        # check the credentials
        identity_changed.send(current_app._get_current_object(),
                              identity=Identity(username))

User Information providers
--------------------------

User information providers should connect to the `identity-loaded` signal to
add any additional information to the Identity instance such as roles. For
example::

    from flask_principal import indentity_loaded, RoleNeed, UserNeed

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        # Get the user information from the db
        user = db.get(identity.name)
        # Update the roles that a user can provide
        for role in user.roles:
            identity.provides.add(RoleNeed(role.name))

API
===



Starting the extension
----------------------

.. autoclass:: flask_principal.Principal
    :members:


Main Types
----------

.. autoclass:: flask_principal.Permission
    :members:

.. autoclass:: flask_principal.Identity
    :members:

.. autoclass:: flask_principal.AnonymousIdentity
    :members:

.. autoclass:: flask_principal.IdentityContext
    :members:



Predefined Need Types
---------------------

.. autoclass:: flask_principal.Need

.. autoclass:: flask_principal.RoleNeed

.. autoclass:: flask_principal.UserNeed

.. autoclass:: flask_principal.ItemNeed


Signals
----------------

.. data:: identity_changed

   Signal sent when the identity for a request has been changed.

.. data:: identity_loaded

   Signal sent when the identity has been initialised for a request.

.. _Flask documentation on signals: http://flask.pocoo.org/docs/signals/


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

