import hashlib
import hmac
import shutil
from functools import wraps
from pathlib import Path
from typing import Mapping
from flask import abort, current_app, make_response, request, send_from_directory
from werkzeug.utils import secure_filename
from xmpp_http_server import app


def security_headers(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        response = make_response(func(*args, **kwargs))
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
        response.headers['X-Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none'"
        response.headers['X-WebKit-CSP'] = "default-src 'none'; frame-ancestors 'none'"
        return response
    return wrapper


def _validate_v1_token(file_path: str, content_size: int, content_type: str,
                       secret_key: str, auth_token: str) -> bool:
    signed_string = f'{file_path} {content_size}'.encode('utf-8')
    mac = hmac.new(secret_key, signed_string, hashlib.sha256)
    calculated_auth_token = mac.hexdigest()
    return hmac.compare_digest(calculated_auth_token, auth_token)


def _validate_v2_token(file_path: str, content_size: int, content_type: str,
                       secret_key: str, auth_token: str) -> bool:
    signed_string = f'{file_path}\0{content_size}\0{content_type}'.encode('utf-8')
    mac = hmac.new(secret_key, signed_string, hashlib.sha256)
    calculated_auth_token = mac.hexdigest()
    return hmac.compare_digest(calculated_auth_token, auth_token)


def _storage_path(path: str) -> Path:
    root_path = Path(current_app.config['XMPP_HTTP_UPLOAD_ROOT'])
    return root_path / secure_filename(path)


def _metadata_path(storage_path: Path) -> Path:
    return storage_path.with_name(f'.{storage_path.name}.metadata')


def _load_metadata(metadata_path: Path) -> Mapping[str, str]:
    metadata = {}
    for line in metadata_path.read_text().splitlines():
        if not line:
            continue
        key, value = line.split(':', 1)
        metadata[key.strip()] = value.strip()
    return metadata


def _is_attachment(content_type: str) -> bool:
    if content_type.startswith('image/'):
        return False
    elif content_type.startswith('video/'):
        return False
    elif content_type.startswith('audio/'):
        return False
    elif content_type == 'text/plain':
        return False
    else:
        return True


@app.route('/<path:path>', methods=['PUT'])
def create(path):
    auth_token_variants = [
        ('v2', _validate_v2_token),
        ('v', _validate_v1_token),
    ]
    for auth_token_key, validate_token in auth_token_variants:
        if auth_token_key in request.args:
            auth_token = request.args[auth_token_key]
            break
    else:
        abort(403, 'No auth token provided')
        return

    secret_key = current_app.config['SECRET_KEY']
    content_size = int(request.headers.get('Content-Length') or 0)
    content_type = request.headers.get('Content-Type') or 'application/octet-stream'

    if not validate_token(path, content_size, content_type, secret_key, auth_token):
        abort(403, 'Invalid auth token')

    # Save file content
    storage_path = _storage_path(path)
    if storage_path.exists():
        abort(409, 'File already exists')
    with storage_path.open('wb') as dest_file:
        shutil.copyfileobj(request.stream, dest_file)

    # Save sidecar file for metadata
    metadata_path = _metadata_path(storage_path)
    with metadata_path.open('w') as metadata_file:
        metadata_file.write(f'Content-Type:{content_type}\n')

    return '', 201


@app.route('/<path:path>', methods=['HEAD'])
@security_headers
def check(path):
    storage_path = _storage_path(path)
    if not storage_path.exists():
        abort(404, 'File not found')
    content_size = storage_path.stat().st_size

    metadata = _load_metadata(_metadata_path(storage_path))
    content_type = metadata.get('Content-Type', 'application/octet-stream')

    return '', 200, {'Content-Size': content_size, 'Content-Type': content_type}


@app.route('/<path:path>', methods=['GET'])
@security_headers
def retrieve(path):
    storage_path = _storage_path(path)

    if not storage_path.exists():
        abort(404, 'File not found')

    metadata = _load_metadata(_metadata_path(storage_path))
    content_type = metadata.get('Content-Type', 'application/octet-stream')

    send_as_attachment = _is_attachment(content_type)

    return send_from_directory(str(storage_path.parent), storage_path.name,
                               mimetype=content_type,
                               as_attachment=send_as_attachment)
