Description
===========

This Flask application implements a server for uploading files according to
`XEP-0363 <https://xmpp.org/extensions/xep-0363.html>`__.

It is supposed to be used with Prosody’s community module
`http_upload_external <https://modules.prosody.im/mod_http_upload_external.html>`__.
Both, version 1 and 2 of the auth token validation are supported.

Installation
============

1.  Clone the repository to a suitable directory

2.  Create a virtual environment:

    .. code::

        python3 -m venv venv

3.  Install the required packages into the virtual environment:

    .. code::

        ./venv/bin/pip install -r requirements.txt

4.  Create a configuration file with the name ``config.py`` in the root of the
    code directory. An example ``config.py.example`` is provided.


Usage
=====

For testing purposes the application can be started with ``run.py``.
For production a WSGI server like ``uWSGI`` or ``mode_wsgi`` is recommended.


Contributing
============

Pull requests are always welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.


License
=======

`AGPL <https://choosealicense.com/licenses/agpl/>`__

By submitting a pull request for this project, you agree to license your
contribution under the AGPL license to this project.
