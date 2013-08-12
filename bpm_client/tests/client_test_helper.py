import contextlib
import socket

from django.core.wsgi import get_wsgi_application
from django.db import close_connection
from django.core import signals

import gevent
import gevent.monkey
import gevent.wsgi


# easy_install https://gevent.googlecode.com/files/gevent-1.0rc2.tar.gz
@contextlib.contextmanager
def run_test_server():
    signals.request_finished.disconnect(close_connection) # share same connection for all requests

    application = get_wsgi_application()
    wsgi_server = gevent.wsgi.WSGIServer(('', 7999), application)
    def serve():
        wsgi_server.serve_forever()

    gevent.spawn(serve)
    gevent.monkey.patch_socket()
    try:
        yield
    finally:
        reload(socket)
        signals.request_finished.connect(close_connection)
        wsgi_server.stop()
