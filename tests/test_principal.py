
from py.test import raises

from flask import Flask, Response

from flaskext.principal import Principal, Permission, Denial, RoleNeed, \
    PermissionDenied, identity_changed, Identity, identity_loaded


def _on_principal_init(sender, identity):
    if identity.name == 'ali':
        identity.provides.add(RoleNeed('admin'))

class ReraiseException(Exception):
    """For checking reraising"""
    
admin_permission = Permission(RoleNeed('admin'))
anon_permission = Permission()

admin_or_editor = Permission(RoleNeed('admin'), RoleNeed('editor'))

editor_permission = Permission(RoleNeed('editor'))

admin_denied = Denial(RoleNeed('admin'))

def mkapp():
    app = Flask(__name__)
    app.secret_key = 'notverysecret'
    app.debug = True

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

    return app


def mkadmin():
    i = Identity('ali')
    return i

def test_deny_with():
    client = mkapp().test_client()
    raises(PermissionDenied, client.open, '/')

def test_deny_view():
    client = mkapp().test_client()
    raises(PermissionDenied, client.open, '/a')

def test_allow_view():
    client = mkapp().test_client()
    assert client.open('/b').data == 'hello'

def test_reraise():
    client = mkapp().test_client()
    raises(ReraiseException, client.open, '/c')

def test_error_view():
    client = mkapp().test_client()
    raises(ReraiseException, client.open, '/d')

def test_permission_union():
    p1 = Permission(('a', 'b'))
    p2 = Permission(('a', 'c'))
    p3 = p1.union(p2)
    assert p1.issubset(p3)
    assert p2.issubset(p3)

def test_permission_union_denial():
    p1 = Permission(('a', 'b'))
    p2 = Denial(('a', 'c'))
    p3 = p1.union(p2)
    assert p1.issubset(p3)
    assert p2.issubset(p3)


def test_opposite_permission():

    p = Permission(('a', 'b'))
    d = p.opposite()
    print d.excludes
    assert ('a', 'b') in d.excludes

def test_identity_changed():
    client = mkapp().test_client()
    assert client.open('/e').data == 'hello'

def test_identity_load():
    client = mkapp().test_client()
    assert client.open('/e').data == 'hello'
    assert client.open('/a').data == 'hello'

def test_or_permissions():
    client = mkapp().test_client()
    assert client.open('/e').data == 'hello'
    assert client.open('/f').data == 'hello'

def test_and_permissions_view_denied():
    client = mkapp().test_client()
    raises(PermissionDenied, client.open, '/g')

def test_and_permissions_view():
    client = mkapp().test_client()
    raises(PermissionDenied, client.open, '/g')

def test_and_permissions_view_with_http_exc():
    client = mkapp().test_client()
    response = client.open("/j")
    assert response.status_code == 403

def test_and_permissions_view_with_http_exc_decorated():
    client = mkapp().test_client()
    response = client.open("/k")
    assert response.status_code == 403

def test_and_permissions_view_with_custom_errhandler():
    app = mkapp()

    @app.errorhandler(403)
    def handle_permission_denied(error):
        assert error.description == admin_permission
        return Response("OK")

    client = app.test_client()
    response = client.open("/k")
    assert response.status_code == 200

def test_permission_and():

    p1 = Permission(RoleNeed('boss'))
    p2 = Permission(RoleNeed('lackey'))

    p3 = p1 & p2
    p4 = p1.union(p2)

    assert p3.needs == p4.needs

def test_contains():

    p1 = Permission(RoleNeed('boss'), RoleNeed('lackey'))
    p2 = Permission(RoleNeed('lackey'))

    assert p2.issubset(p1)
    assert p2 in p1

def test_permission_bool():

    client = mkapp().test_client()
    response = client.open('/l')
    assert response.status_code == 200
    assert 'not admin' in response.data
    assert 'now admin' in response.data


def test_denied_passes():

    client = mkapp().test_client()
    response = client.open("/m")
    assert response.status_code == 200

def test_denied_fails():

    client = mkapp().test_client()
    raises(PermissionDenied, client.open, '/n')
