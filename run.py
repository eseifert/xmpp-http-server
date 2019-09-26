#!/usr/bin/env python3
"""
This starts the application with Flask’s webserver.
Use this for testing only, Flask’s server is not fit for production.
"""
from xmpp_http_server import app

if __name__ == '__main__':
    app.run(debug=True)
