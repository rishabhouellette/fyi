"""
FYI Social ∞ - Local OAuth Service
THE NGROK KILLER - No more tunneling! Uses localhost + custom protocol
"""

from flask import Flask, request, jsonify
from typing import Callable, Optional
import threading
import webbrowser
from urllib.parse import urlencode, urlparse
from pathlib import Path
import datetime as dt
import ipaddress

from backend.config import get_config

config = get_config()


class LocalOAuthServer:
    """
    Local OAuth server that runs on https://localhost:5000
    Uses custom fyi:// protocol to capture redirects
    NO NGROK NEEDED!
    """
    
    def __init__(self, port: int = 5000):
        redirect_uri = config.OAUTH_REDIRECT_URI or f"https://127.0.0.1:{port}/oauth/callback"
        parsed = urlparse(redirect_uri)

        self.scheme = parsed.scheme or 'https'
        self.host = parsed.hostname or '127.0.0.1'
        self.port = parsed.port or port
        self.redirect_path = parsed.path or '/oauth/callback'
        self.redirect_uri = f"{self.scheme}://{self.host}:{self.port}{self.redirect_path}"
        self.app = Flask(__name__)
        self.server_thread = None
        self.callback_handlers = {}
        self.cert_path = Path("desktop_callback_cert.pem")
        self.key_path = Path("desktop_callback_key.pem")
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes for OAuth"""
        
        @self.app.route('/oauth/callback')
        def oauth_callback():
            """Handle OAuth callback from platforms"""
            # Get platform from state parameter
            state = request.args.get('state', '')
            platform = state.split(':')[0] if ':' in state else 'unknown'
            
            # Get authorization code or error
            code = request.args.get('code')
            error = request.args.get('error')
            
            if error:
                return f'''
                <html>
                <head>
                    <title>FYI Social ∞ - OAuth Error</title>
                    <style>
                        body {{
                            font-family: 'Satoshi', sans-serif;
                            background: linear-gradient(180deg, #0a0a1f, #000000);
                            color: white;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            height: 100vh;
                            margin: 0;
                        }}
                        .container {{
                            text-align: center;
                            padding: 40px;
                            background: rgba(10, 10, 31, 0.09);
                            backdrop-filter: blur(12px);
                            border: 1px solid rgba(0, 242, 255, 0.4);
                            border-radius: 16px;
                            box-shadow: 0 0 30px rgba(0, 242, 255, 0.4);
                        }}
                        h1 {{ color: #ff006e; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>❌ Authentication Failed</h1>
                        <p>Error: {error}</p>
                        <p>You can close this window.</p>
                    </div>
                </body>
                </html>
                '''
            
            # Call registered handler
            if platform in self.callback_handlers:
                try:
                    result = self.callback_handlers[platform](code, request.args)
                    
                    return f'''
                    <html>
                    <head>
                        <title>FYI Social ∞ - Connected!</title>
                        <style>
                            body {{
                                font-family: 'Satoshi', sans-serif;
                                background: linear-gradient(180deg, #0a0a1f, #000000);
                                color: white;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                height: 100vh;
                                margin: 0;
                            }}
                            .container {{
                                text-align: center;
                                padding: 40px;
                                background: rgba(10, 10, 31, 0.09);
                                backdrop-filter: blur(12px);
                                border: 1px solid rgba(0, 242, 255, 0.4);
                                border-radius: 16px;
                                box-shadow: 0 0 30px rgba(0, 242, 255, 0.4);
                            }}
                            h1 {{ 
                                background: linear-gradient(90deg, #00f2ff, #8b00ff);
                                -webkit-background-clip: text;
                                -webkit-text-fill-color: transparent;
                            }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>✅ Account Connected!</h1>
                            <p>{platform.title()} account linked successfully.</p>
                            <p>You can close this window and return to FYI Social ∞</p>
                        </div>
                        <script>
                            // Auto-close after 3 seconds
                            setTimeout(() => window.close(), 3000);
                        </script>
                    </body>
                    </html>
                    '''
                except Exception as e:
                    return jsonify({'error': str(e)}), 500
            
            return jsonify({'error': 'No handler registered'}), 500
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return jsonify({'status': 'ok', 'service': 'FYI OAuth Server'})
    
    def register_callback(self, platform: str, handler: Callable):
        """Register a callback handler for a platform"""
        self.callback_handlers[platform] = handler
    
    def _ensure_ssl_certificates(self):
        """Create self-signed certs for localhost if missing"""
        if self.cert_path.exists() and self.key_path.exists():
            return
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.backends import default_backend
        except ImportError as exc:
            raise RuntimeError("cryptography module is required for HTTPS OAuth. Install it with 'pip install cryptography'.") from exc

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, u"FYI OAuth Localhost"),
        ])

        alt_names = [
            x509.DNSName(u"localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]
        if self.host not in {"localhost", "127.0.0.1"}:
            alt_names.append(x509.DNSName(self.host))

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(dt.datetime.utcnow())
            .not_valid_after(dt.datetime.utcnow() + dt.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName(alt_names), critical=False)
            .sign(key, hashes.SHA256(), default_backend())
        )

        self.key_path.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        self.cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        print("✅ Generated HTTPS certificate for local OAuth server")

    def start(self):
        """Start the OAuth server in background thread"""
        if self.server_thread and self.server_thread.is_alive():
            return
        
        def run_server():
            try:
                self._ensure_ssl_certificates()
            except RuntimeError as exc:
                print(f"❌ {exc}")
                return
            self.app.run(
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                ssl_context=(str(self.cert_path), str(self.key_path))
            )
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        print(f"🔐 OAuth server started at {self.redirect_uri}")
    
    def get_authorization_url(self, platform: str, auth_url: str, params: dict) -> str:
        """Generate OAuth authorization URL with proper redirect"""
        params['redirect_uri'] = self.redirect_uri
        params['state'] = f'{platform}:{params.get("state", "")}'
        
        return f"{auth_url}?{urlencode(params)}"
    
    def open_authorization_url(self, url: str):
        """Open authorization URL in browser"""
        webbrowser.open(url)


# Global OAuth server instance
_oauth_server = None

def get_oauth_server() -> LocalOAuthServer:
    """Get global OAuth server instance"""
    global _oauth_server
    if _oauth_server is None:
        _oauth_server = LocalOAuthServer(port=config.API_PORT)
    return _oauth_server
