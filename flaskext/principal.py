# -*- coding: utf-8 -*-
"""
    flaskext.principal
    ~~~~~~~~~~~~~~~~~~

    Description of the module goes here...

    :copyright: (c) 2010 by Ali Afshar.
    :license: MIT, see LICENSE for more details.



"""
import sys

from flask import g, session

from functools import partial, wraps
from collections import namedtuple
from blinker import Namespace


signals = Namespace()


identity_changed = signals.signal('identity-set')

#: Signal sent when the principal is insitialised during a request.
#: Implementors should use this to mutate the identity by adding to the
#: provides set
identity_loaded = signals.signal('principal-initialized')

# A need
Need = namedtuple('Need', ['method', 'value'])

UserNeed = partial(Need, 'name')
RoleNeed = partial(Need, 'role')


class PermissionDenied(RuntimeError):
    """Permission denied to the resource"""


class Identity(object):

    def __init__(self, name, auth_type=''):
        self.name = name
        self.auth_type = auth_type
        self.provides = set()

    def can(self, permission):
        if not permission.needs:
            return True
        else:
            return permission.needs.intersection(self.provides)


class AnonymousIdentity(Identity):

    def __init__(self):
        Identity.__init__(self, 'anon')


class Principal(object):

    def __init__(self, permission):
        self.permission = permission

    @property
    def identity(self):
        return g.identity

    def can(self):
        return self.identity.can(self.permission)

    def __call__(self, f):
        @wraps(f)
        def _decorated(*args, **kw):
            self.__enter__()
            exc = (None, None, None)
            try:
                result = f(*args, **kw)
            except Exception:
                exc = sys.exc_info()
            self.__exit__(*exc)
            return result
        return _decorated

    def __enter__(self):
        # check the permission here
        if not self.can():
            raise PermissionDenied(self.permission)

    def __exit__(self, *exc):
        if exc != (None, None, None):
            cls, val, tb = exc
            raise cls, val, tb
        return False


class Permission(object):

    def __init__(self, *needs):
        self.needs = set(needs)

    def require(self):
        """Create a principal for this permission.
        """
        return Principal(self)

    def union(self, other):
        """Create a new permission with the requirements of the union of this
        and other.

        :param other: The other permission
        """
        return Permission(*self.needs.union(other.needs))

    def issubset(self, other):
        """Whether this permission needs are a subset of another

        :param other: The other permission
        """
        return self.needs.issubset(other.needs)


def set_identity(identity):
    session['identity.name'] = identity.name
    session['identity.auth_type'] = identity.auth_type
    session.modified = True
    _load_identity()

def _on_identity_changed(sender, identity):
    set_identity(identity)

def _load_identity():
    if 'identity.name' in session and 'identity.auth_type' in session:
        identity = Identity(session['identity.name'],
                            session['identity.auth_type'])
        g.identity = identity
    else:
        g.identity = AnonymousIdentity()
    identity_loaded.send(g.identity, identity=g.identity)

def _on_before_request():
    _load_identity()

def init_principal(app):
    app.before_request(_on_before_request)
    identity_changed.connect(_on_identity_changed)


