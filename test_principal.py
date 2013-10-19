
from __future__ import with_statement

import unittest

from flask import Flask, Response

from flask_principal import BasePermission, OrPermission, AndPermission
from flask_principal import Principal, Permission, Denial, RoleNeed, \
    PermissionDenied, identity_changed, Identity, identity_loaded

anon_permission = Permission()
admin_permission = Permission(RoleNeed('admin'))
admin_or_editor = Permission(RoleNeed('admin'), RoleNeed('editor'))
editor_permission = Permission(RoleNeed('editor'))
manager_permission = Permission(RoleNeed('manager'))

admin_denied = Denial(RoleNeed('admin'))


class RolenamePermission(BasePermission):
    def __init__(self, role):
        self.role = role
    def allows(self, identity):
        return RoleNeed(self.role) in identity.provides

admin_role_permission = RolenamePermission('admin')
editor_role_permission = RolenamePermission('editor')
manager_role_permission = RolenamePermission('manager')
reviewer_role_permission = RolenamePermission('reviewer')


def _on_principal_init(sender, identity):
    role_map = {
        'ali': (RoleNeed('admin'),),
        'admin': (RoleNeed('admin'),),
        'editor': (RoleNeed('editor'),),
        'reviewer': (RoleNeed('reviewer'),),
        'admin_editor': (RoleNeed('editor'), RoleNeed('admin')),
        'manager': (RoleNeed('manager'),),
        'manager_editor': (RoleNeed('editor'), RoleNeed('manager')),
        'reviewer_editor': (RoleNeed('editor'), RoleNeed('reviewer')),
    }

    roles = role_map.get(identity.id)
    if roles:
        for role in roles:
            identity.provides.add(role)


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

    @app.route('/and_base_fail')
    def and_base_fail():
        i = mkadmin()
        admin_and_editor_rp = (admin_role_permission & editor_role_permission)
        identity_changed.send(app, identity=i)
        with admin_and_editor_rp.require():
            return Response('fail')

    @app.route('/and_base_success')
    def and_base_success():
        i = Identity('admin_editor')
        identity_changed.send(app, identity=i)
        # using both formerly default, calling parent __and__
        admin_and_editor_rp = (admin_permission & editor_permission)
        with admin_and_editor_rp.require():
            return Response('good')

    @app.route('/and_mixed1')
    def and_mixed1():
        admin_and_editor_mixed = (admin_role_permission & editor_permission)
        i = Identity('editor')
        identity_changed.send(app, identity=i)
        with admin_and_editor_mixed.require():
            return Response('fail')

    @app.route('/and_mixed2')  # reversed type of the above.
    def and_mixed2():
        admin_and_editor_mixed = (admin_permission & editor_role_permission)
        i = Identity('admin_editor')
        identity_changed.send(app, identity=i)
        with admin_and_editor_mixed.require():
            return Response('good')

    @app.route('/or_base')
    def or_base():
        i = mkadmin()
        admin_or_editor_rp = (admin_role_permission | editor_role_permission)
        identity_changed.send(app, identity=i)
        with admin_or_editor_rp.require():
            return Response('hello')

    @app.route('/or_mixed1')
    def or_mixed1():
        result = []
        admin_or_editor_mixed = (admin_role_permission | editor_permission)

        i = Identity('admin')
        identity_changed.send(app, identity=i)
        with admin_or_editor_mixed.require():
            result.append('good')

        i = Identity('editor')
        identity_changed.send(app, identity=i)
        with admin_or_editor_mixed.require():
            result.append('good')

        return Response(''.join(result))

    @app.route('/or_mixed2')  # reversed type of the above.
    def or_mixed2():
        result = []
        admin_or_editor_mixed = (admin_permission | editor_role_permission)

        i = Identity('admin')
        identity_changed.send(app, identity=i)
        with admin_or_editor_mixed.require():
            result.append('good')

        i = Identity('editor')
        identity_changed.send(app, identity=i)
        with admin_or_editor_mixed.require():
            result.append('good')

        return Response(''.join(result))

    @app.route('/mixed_ops_fail')
    def mixed_ops_fail():
        result = []
        mixed_perms = (admin_permission | manager_permission |
            (reviewer_role_permission & editor_role_permission))

        i = Identity('editor')
        identity_changed.send(app, identity=i)
        with mixed_perms.require():
            result.append('fail')

    @app.route('/mixed_ops1')
    def mixed_ops1():
        result = []
        mixed_perms = (admin_permission | manager_permission |
            (reviewer_role_permission & editor_role_permission))

        i = Identity('reviewer_editor')
        identity_changed.send(app, identity=i)
        with mixed_perms.require():
            result.append('good')

        i = Identity('manager')
        identity_changed.send(app, identity=i)
        with mixed_perms.require():
            result.append('good')

        i = Identity('admin')
        identity_changed.send(app, identity=i)
        with mixed_perms.require():
            result.append('good')

        return Response(''.join(result))

    @app.route('/mixed_ops2')
    def mixed_ops2():
        result = []
        mixed_perms = ((admin_permission & editor_permission) |
            (manager_role_permission & editor_role_permission))

        i = Identity('manager_editor')
        identity_changed.send(app, identity=i)
        if mixed_perms.can():
            result.append('good')

        i = Identity('manager')
        identity_changed.send(app, identity=i)
        if mixed_perms.can():
            result.append('bad')

        i = Identity('editor')
        identity_changed.send(app, identity=i)
        if mixed_perms.can():
            result.append('bad')

        i = Identity('admin_editor')
        identity_changed.send(app, identity=i)
        if mixed_perms.can():
            result.append('good')

        i = Identity('admin')
        identity_changed.send(app, identity=i)
        if mixed_perms.can():
            result.append('bad')

        return Response(''.join(result))

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
            s.append("not admin_or_editor")
        if not (admin_permission or editor_permission):
            s.append("not (admin or editor)")

        i = Identity('ali')
        identity_changed.send(app, identity=i)
        if admin_or_editor:
            s.append("now admin_or_editor")
        if admin_permission or editor_permission:
            s.append("now admin or editor")
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

    @app.route("/o2")
    def o2():
        (admin_permission | editor_permission).test()
        return Response("OK")

    @app.route("/o3")
    def o3():
        i = mkadmin()
        identity_changed.send(app, identity=i)
        (admin_permission | editor_permission).test()
        return Response("OK")

    @app.route("/p")
    def p():
        admin_or_editor.test(404)
        return Response("OK")

    return app


def mkadmin():
    i = Identity('ali')
    return i


class BasePermissionUnitTests(unittest.TestCase):

    def test_or_permission(self):
        admin_or_editor_rp = (admin_role_permission | editor_role_permission)
        self.assertTrue(isinstance(admin_or_editor_rp, OrPermission))
        self.assertEqual(admin_or_editor_rp.permissions,
            set([admin_role_permission, editor_role_permission]))

    def test_and_permission(self):
        admin_and_editor_rp = (admin_role_permission & editor_role_permission)
        self.assertTrue(isinstance(admin_and_editor_rp, AndPermission))
        self.assertEqual(admin_and_editor_rp.permissions,
            set([admin_role_permission, editor_role_permission]))

    # TODO test manual construction


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

    def test_permission_difference(self):
        p1 = Permission(RoleNeed('boss'))
        p2 = Permission(RoleNeed('lackey'))

        p3 = p1 - p2
        p4 = p1.difference(p2)

        # parity with set operations
        p3needs = p1.needs - p2.needs

        assert p3.needs == p4.needs
        assert p3.needs == p3needs

    def test_permission_difference_excludes(self):
        p1 = Permission(RoleNeed('boss')).reverse()
        p2 = Permission(RoleNeed('lackey')).reverse()

        p3 = p1 - p2
        p4 = p1.difference(p2)

        # parity with set operations
        p3excludes = p1.excludes - p2.excludes

        assert p3.excludes == p4.excludes
        assert p3.excludes == p3excludes

    def test_permission_or(self):
        p1 = Permission(RoleNeed('boss'), RoleNeed('lackey'))
        p2 = Permission(RoleNeed('lackey'), RoleNeed('underling'))

        p3 = p1 | p2
        p4 = p1.union(p2)

        # Ensure that an `or` between sets also result in the expected
        # behavior.  As expected, as "any of which must be present to 
        # access a resource".
        p3needs = p1.needs | p2.needs

        assert p3.needs == p4.needs
        assert p3.needs == p3needs

    def test_permission_or_excludes(self):
        p1 = Permission(RoleNeed('boss'), RoleNeed('lackey')).reverse()
        p2 = Permission(RoleNeed('lackey'), RoleNeed('underling')).reverse()

        p3 = p1 | p2
        p4 = p1.union(p2)

        # Ensure that an `or` between sets also result in the expected
        # behavior.  As expected, as "any of which must be present to 
        # access a resource".
        p3excludes = p1.excludes | p2.excludes

        assert p3.excludes == p4.excludes
        assert p3.excludes == p3excludes

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

    def test_base_or_permissions(self):
        assert self.client.open('/or_base').data == b'hello'

    def test_mixed_or_permissions(self):
        assert self.client.open('/or_mixed1').data == b'goodgood'
        assert self.client.open('/or_mixed2').data == b'goodgood'

    def test_base_and_permissions(self):
        self.assertRaises(PermissionDenied, self.client.open, '/and_base_fail')
        self.assertEqual(self.client.open('/and_base_success').data, b'good')

    def test_mixed_and_permissions(self):
        self.assertRaises(PermissionDenied, self.client.open, '/and_mixed1')
        self.assertEqual(self.client.open('/and_mixed2').data, b'good')

    def test_mixed_and_or_permissions_fail(self):
        self.assertRaises(PermissionDenied,
            self.client.open, '/mixed_ops_fail')

    def test_mixed_and_or_permissions(self):
        self.assertEqual(self.client.open('/mixed_ops1').data, b'goodgoodgood')
        self.assertEqual(self.client.open('/mixed_ops2').data, b'goodgood')

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
        assert b'not admin_or_editor' in response.data
        assert b'not (admin or editor)' in response.data
        assert b'now admin_or_editor' in response.data
        assert b'now admin or editor' in response.data

    def test_denied_passes(self):
        response = self.client.open("/m")
        assert response.status_code == 200

    def test_denied_fails(self):
        self.assertRaises(PermissionDenied, self.client.open, '/n')

    def test_permission_test(self):
        self.assertRaises(PermissionDenied, self.client.open, '/o')

    def test_permission_operator_test(self):
        self.assertRaises(PermissionDenied, self.client.open, '/o2')

        response = self.client.open('/o3')
        assert response.status_code == 200
        assert response.data == b'OK'

    def test_permission_test_with_http_exc(self):
        response = self.client.open("/p")
        assert response.status_code == 404


class FactoryMethodPrincipalApplicationTests(PrincipalApplicationTests):
    def setUp(self):
        self.client = mkapp(with_factory=True).test_client()
