import os
import logging
import re
import eventlet
eventlet.monkey_patch()

from flask import Flask, jsonify, render_template, request, abort
from flask_cors import CORS
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.middleware.proxy_fix import ProxyFix
from socketio import WSGIApp
from dotenv import load_dotenv

load_dotenv()

# --- Imports local modules ---
from extensions import limiter
from api.analyze import analyze_endpoint
from api.admin import admin_endpoint

# Sub-apps (Dương Dev ecosystem)
from duongdev.TO1_Chat.app import app as to1_chat_app, socketio as to1_chat_socketio
from duongdev.anmqpan.app import app as qpan_app, socketio as qpan_socketio
from duongdev.minhthy.app import app as minhthy_app, socketio as minhthy_socketio
from duongdev.share.app import app as share_app, socketio as share_socketio
from duongdev.macos.app import app as us_app, socketio as us_socketio
from duongdev.that_thach.app import app as that_thach_app, socketio as that_thach_socketio
from duongdev.tarot.app import app as tarot_app

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = os.environ.get('SECRET_KEY', 'cybershield-secret-2026')
CORS(app)
limiter.init_app(app)

# --- FIREWALL & SECURITY ---
@app.before_request
def firewall():
    path = request.path.lower()
    sensitive_patterns = [r'\.env', r'\.git', r'\.db', r'\.py', r'secrets/', r'config\.json']
    attack_patterns = [r'\/wp-', r'\/phpmyadmin', r'\.\.\/', r'etc\/passwd']
    
    if any(re.search(p, path) for p in sensitive_patterns + attack_patterns):
        logger.warning(f"🚨 [FIREWALL] Blocked IP {request.remote_addr} -> {path}")
        abort(403)

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Content-Security-Policy'] = "default-src 'self' * 'unsafe-inline' 'unsafe-eval' data: blob:;"
    return response

# --- ROUTES ---
app.register_blueprint(analyze_endpoint, url_prefix='/api')
app.register_blueprint(admin_endpoint)

@app.route('/')
def home(): return render_template('index.html')

@app.route('/health')
def health(): return jsonify({'status': '🟢 Online', 'version': '2.0-Alpha'})

# --- WSGI DISPATCHER (Sub-apps) ---
class FlaskAppMiddleware:
    def __init__(self, wsgi_app, flask_app):
        self.wsgi_app = wsgi_app
        self.flask_app = flask_app
    def __call__(self, environ, start_response):
        environ['flask.app'] = self.flask_app
        return self.wsgi_app(environ, start_response)

def wrap_socketio(sio, flask_app):
    return FlaskAppMiddleware(WSGIApp(sio.server, flask_app), flask_app)

application = DispatcherMiddleware(app, {
    '/duongdev/to1-chat': wrap_socketio(to1_chat_socketio, to1_chat_app),
    '/duongdev/qpan': wrap_socketio(qpan_socketio, qpan_app),
    '/duongdev/minhthy': wrap_socketio(minhthy_socketio, minhthy_app),
    '/duongdev/share': wrap_socketio(share_socketio, share_app),
    '/duongdev/macos': wrap_socketio(us_socketio, us_app),
    '/duongdev/that-thach': wrap_socketio(that_thach_socketio, that_thach_app),
    '/duongdev/tarot': tarot_app
})

if __name__ == '__main__':
    from eventlet import wsgi
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 CyberShield Sentinel active on port {port}")
    wsgi.server(eventlet.listen(('', port)), application)
