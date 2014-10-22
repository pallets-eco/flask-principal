
from __future__ import with_statement

import unittest

from flask import Flask, Response

from flask_principal import Principal, Permission, Denial, RoleNeed, \
    PermissionDenied, identity_changed, Identity, identity_loaded, \
    OrPermission

anon_permission = Permission()
admin_permission = Permission(RoleNeed('admin'))
admin_or_editor = OrPermission(RoleNeed('admin'), RoleNeed('editor'))
editor_permission = Permission(RoleNeed('editor'))
admin_denied = Denial(RoleNeed('admin'))


def _on_principal_init(sender, identity):
    if identity.id == 'ali':
        identity.provides.add(RoleNeed('admin'))


class ReraiseException(Exception):
    """For checking reraising"""


def mkapp(with_factory=False):
    app = Flask(__name__)
    app.secret_key = 'notverysecret'
    app.debug = True

    if with_factory:
        p = Principal()
        p.init_app(app)
    else:
        p = Principal(app)

    identity_loaded.connect(_on_principal_init)

    @app.route('/')
    def index():
        with admin_permission.require():
            pass
        return Response('hello')

    @app.route('/a')
    @admin_permission.require()
    def a():
        return Response('hello')

    @app.route('/b')
    @anon_permission.require()
    def b():
        return Response('hello')

    @app.route('/c')
    def c():
        with anon_permission.require():
            raise ReraiseException

    @app.route('/d')
    @anon_permission.require()
    def d():
        raise ReraiseException

    @app.route('/e')
    def e():
        i = mkadmin()
        identity_changed.send(app, identity=i)
        with admin_permission.require():
            return Response('hello')

    @app.route('/f')
    def f():
        i = mkadmin()
        identity_changed.send(app, identity=i)
        with admin_or_editor.require():
            return Response('hello')

    @app.route('/g')
    @admin_permission.require()
    @editor_permission.require()
    def g():
        return Response('hello')

    @app.route('/h')
    def h():
        i = Identity('james')
        identity_changed.send(app, identity=i)
        with admin_permission.require():
            with editor_permission.require():
                pass

    @app.route('/j')
    def j():
        i = Identity('james')
        identity_changed.send(app, identity=i)
        with admin_permission.require(403):
            with editor_permission.require(403):
                pass

    @app.route('/k')
    @admin_permission.require(403)
    def k():
        return Response('hello')

    @app.route('/l')
    def l():
        s = []
        if not admin_or_editor:
            s.append("not admin")

        i = Identity('ali')
        identity_changed.send(app, identity=i)
        if admin_or_editor:
            s.append("now admin")
        return Response('\n'.join(s))

    @app.route("/m")
    def m():
        with admin_denied.require():
            pass

        return Response("OK")

    @app.route("/n")
    def n():
        i = mkadmin()
        identity_changed.send(app, identity=i)
        with admin_denied.require():
            pass

        return Response("OK")

    @app.route("/o")
    def o():
        admin_or_editor.test()
        return Response("OK")

    @app.route("/p")
    def p():
        admin_or_editor.test(404)
        return Response("OK")

    return app


def mkadmin():
    i = Identity('ali')
    return i


class PrincipalUnitTests(unittest.TestCase):

    def test_permission_union(self):
        p1 = Permission(('a', 'b'))
        p2 = Permission(('a', 'c'))
        p3 = p1.union(p2)
        assert p1.issubset(p3)
        assert p2.issubset(p3)

    def test_permission_difference(self):
        p1 = Permission(('a', 'b'), ('a', 'c'))
        p2 = Permission(('a', 'c'), ('d', 'e'))
        p3 = p1.difference(p2)
        assert p3.needs == set([('a', 'b')])
        p4 = p2.difference(p1)
        assert p4.needs == set([('d', 'e')])

    def test_permission_union_denial(self):
        p1 = Permission(('a', 'b'))
        p2 = Denial(('a', 'c'))
        p3 = p1.union(p2)
        assert p1.issubset(p3)
        assert p2.issubset(p3)

    def test_permission_difference_denial(self):
        p1 = Denial(('a', 'b'), ('a', 'c'))
        p2 = Denial(('a', 'c'), ('d', 'e'))
        p3 = p1.difference(p2)
        assert p3.excludes == set([('a', 'b')])
        p4 = p2.difference(p1)
        assert p4.excludes == set([('d', 'e')])

    def test_reverse_permission(self):
        p = Permission(('a', 'b'))
        d = p.reverse()
        assert ('a', 'b') in d.excludes

    def test_permission_and(self):
        p1 = Permission(RoleNeed('boss'))
        p2 = Permission(RoleNeed('lackey'))

        p3 = p1 & p2
        p4 = p1.union(p2)

        assert p3.needs == p4.needs

    def test_permission_or(self):
        p1 = Permission(RoleNeed('boss'), RoleNeed('lackey'))
        p2 = Permission(RoleNeed('lackey'), RoleNeed('underling'))

        p3 = p1 | p2
        p4 = p1.difference(p2)

        assert p3.needs == p4.needs

    def test_contains(self):
        p1 = Permission(RoleNeed('boss'), RoleNeed('lackey'))
        p2 = Permission(RoleNeed('lackey'))

        assert p2.issubset(p1)
        assert p2 in p1


class PrincipalApplicationTests(unittest.TestCase):

    def setUp(self):
        self.client = mkapp().test_client()

    def test_deny_with(self):
        self.assertRaises(PermissionDenied, self.client.open, '/')

    def test_deny_view(self):
        self.assertRaises(PermissionDenied, self.client.open, '/a')

    def test_allow_view(self):
        assert self.client.open('/b').data == b'hello'

    def test_reraise(self):
        self.assertRaises(ReraiseException, self.client.open, '/c')

    def test_error_view(self):
        self.assertRaises(ReraiseException, self.client.open, '/d')

    def test_identity_changed(self):
        assert self.client.open('/e').data == b'hello'

    def test_identity_load(self):
        assert self.client.open('/e').data == b'hello'
        assert self.client.open('/a').data == b'hello'

    def test_or_permissions(self):
        assert self.client.open('/e').data == b'hello'
        assert self.client.open('/f').data == b'hello'

    def test_and_permissions_view_denied(self):
        self.assertRaises(PermissionDenied, self.client.open, '/g')

    def test_and_permissions_view(self):
        self.assertRaises(PermissionDenied, self.client.open, '/g')

    def test_and_permissions_view_with_http_exc(self):
        response = self.client.open("/j")
        assert response.status_code == 403

    def test_and_permissions_view_with_http_exc_decorated(self):
        response = self.client.open("/k")
        assert response.status_code == 403

    def test_and_permissions_view_with_custom_errhandler(self):
        app = mkapp()

        @app.errorhandler(403)
        def handle_permission_denied(error):
            assert error.description == admin_permission
            return Response("OK")

        self.client = app.test_client()
        response = self.client.open("/k")
        assert response.status_code == 200

    def test_permission_bool(self):
        response = self.client.open('/l')
        assert response.status_code == 200
        assert b'not admin' in response.data
        assert b'now admin' in response.data

    def test_denied_passes(self):
        response = self.client.open("/m")
        assert response.status_code == 200

    def test_denied_fails(self):
        self.assertRaises(PermissionDenied, self.client.open, '/n')

    def test_permission_test(self):
        self.assertRaises(PermissionDenied, self.client.open, '/o')

    def test_permission_test_with_http_exc(self):
        response = self.client.open("/p")
        assert response.status_code == 404


class FactoryMethodPrincipalApplicationTests(PrincipalApplicationTests):
    def setUp(self):
        self.client = mkapp(with_factory=True).test_client()
