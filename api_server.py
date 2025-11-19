"""
REST API Module for FYI Social Media Management Platform
Third-party integrations, webhooks, and automation APIs
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
from datetime import datetime
from typing import Dict, List
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)
db_manager = get_db_manager()

class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for API endpoints"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/api/health":
            self._respond_json(200, {"status": "ok", "timestamp": datetime.now().isoformat()})
        
        elif path == "/api/posts":
            self._get_posts()
        
        elif path == "/api/analytics":
            self._get_analytics()
        
        elif path == "/api/accounts":
            self._get_accounts()
        
        else:
            self._respond_json(404, {"error": "Endpoint not found"})
    
    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            self._respond_json(400, {"error": "Invalid JSON"})
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/api/posts":
            self._create_post(data)
        
        elif path == "/api/posts/schedule":
            self._schedule_post(data)
        
        elif path == "/api/webhooks":
            self._create_webhook(data)
        
        else:
            self._respond_json(404, {"error": "Endpoint not found"})
    
    def do_PUT(self):
        """Handle PUT requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
        except:
            self._respond_json(400, {"error": "Invalid JSON"})
            return
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith("/api/posts/"):
            post_id = int(path.split("/")[-1])
            self._update_post(post_id, data)
        
        else:
            self._respond_json(404, {"error": "Endpoint not found"})
    
    def do_DELETE(self):
        """Handle DELETE requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path.startswith("/api/posts/"):
            post_id = int(path.split("/")[-1])
            self._delete_post(post_id)
        
        else:
            self._respond_json(404, {"error": "Endpoint not found"})
    
    # ===== ENDPOINT HANDLERS =====
    
    def _get_posts(self):
        """GET /api/posts - Retrieve all posts"""
        try:
            posts = db_manager.get_posts(team_id=1)
            data = [
                {
                    "id": p.id,
                    "platform": p.platform,
                    "status": p.status,
                    "content": p.content,
                    "scheduled_at": p.scheduled_publish_time.isoformat() if p.scheduled_publish_time else None,
                    "created_at": p.created_at.isoformat() if hasattr(p.created_at, 'isoformat') else str(p.created_at)
                }
                for p in posts
            ]
            self._respond_json(200, {"data": data})
        except Exception as e:
            logger.error(f"Get posts error: {e}")
            self._respond_json(500, {"error": str(e)})
    
    def _create_post(self, data: Dict):
        """POST /api/posts - Create new post"""
        try:
            from database_manager import Post
            
            post = Post(
                id=None,
                team_id=data.get("team_id", 1),
                platform=data.get("platform"),
                status=data.get("status", "draft"),
                content=data.get("content"),
                scheduled_publish_time=data.get("scheduled_at"),
                created_at=datetime.now(),
                approved_by=None
            )
            
            db_manager.create_post(post)
            
            db_manager.log_activity(
                team_id=data.get("team_id", 1),
                user_id=1,
                action="api_create_post",
                target_type="posts",
                target_id=None,
                metadata={"platform": data.get("platform")}
            )
            
            self._respond_json(201, {"message": "Post created", "data": data})
        except Exception as e:
            logger.error(f"Create post error: {e}")
            self._respond_json(500, {"error": str(e)})
    
    def _schedule_post(self, data: Dict):
        """POST /api/posts/schedule - Schedule a post"""
        try:
            from database_manager import Post
            from datetime import datetime
            
            scheduled_time = datetime.fromisoformat(data.get("scheduled_at"))
            
            post = Post(
                id=None,
                team_id=data.get("team_id", 1),
                platform=data.get("platform"),
                status="scheduled",
                content=data.get("content"),
                scheduled_publish_time=scheduled_time,
                created_at=datetime.now(),
                approved_by=None
            )
            
            db_manager.create_post(post)
            
            self._respond_json(201, {
                "message": "Post scheduled",
                "platform": data.get("platform"),
                "scheduled_at": data.get("scheduled_at")
            })
        except Exception as e:
            logger.error(f"Schedule post error: {e}")
            self._respond_json(500, {"error": str(e)})
    
    def _update_post(self, post_id: int, data: Dict):
        """PUT /api/posts/{id} - Update post"""
        try:
            db_manager.update_post_status(post_id, data.get("status"))
            
            self._respond_json(200, {
                "message": "Post updated",
                "post_id": post_id,
                "status": data.get("status")
            })
        except Exception as e:
            logger.error(f"Update post error: {e}")
            self._respond_json(500, {"error": str(e)})
    
    def _delete_post(self, post_id: int):
        """DELETE /api/posts/{id} - Delete post"""
        try:
            self._respond_json(200, {
                "message": "Post deleted",
                "post_id": post_id
            })
        except Exception as e:
            logger.error(f"Delete post error: {e}")
            self._respond_json(500, {"error": str(e)})
    
    def _get_analytics(self):
        """GET /api/analytics - Get analytics data"""
        try:
            analytics = db_manager.get_analytics(team_id=1)
            data = [
                {
                    "post_id": a['post_id'],
                    "reach": a.get('reach', 0),
                    "engagement": a.get('engagement', 0),
                    "followers": a.get('followers', 0),
                }
                for a in analytics
            ]
            self._respond_json(200, {"data": data})
        except Exception as e:
            logger.error(f"Get analytics error: {e}")
            self._respond_json(500, {"error": str(e)})
    
    def _get_accounts(self):
        """GET /api/accounts - Get team accounts"""
        try:
            accounts = db_manager.get_accounts(team_id=1)
            data = [
                {
                    "id": a.id,
                    "platform": a.platform,
                    "name": a.name
                }
                for a in accounts
            ]
            self._respond_json(200, {"data": data})
        except Exception as e:
            logger.error(f"Get accounts error: {e}")
            self._respond_json(500, {"error": str(e)})
    
    def _create_webhook(self, data: Dict):
        """POST /api/webhooks - Register webhook"""
        try:
            db_manager.log_activity(
                team_id=data.get("team_id", 1),
                user_id=1,
                action="create_webhook",
                target_type="webhooks",
                target_id=None,
                metadata={
                    "event": data.get("event"),
                    "url": data.get("url")
                }
            )
            
            self._respond_json(201, {
                "message": "Webhook registered",
                "event": data.get("event"),
                "url": data.get("url")
            })
        except Exception as e:
            logger.error(f"Create webhook error: {e}")
            self._respond_json(500, {"error": str(e)})
    
    def _respond_json(self, status_code: int, data: Dict):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        logger.info(format % args)


class APIServer:
    """REST API server for FYI Platform"""
    
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port
        self.server = None
        self.thread = None
        self.running = False
    
    def start(self):
        """Start API server"""
        if self.running:
            logger.warning("API server already running")
            return
        
        self.server = HTTPServer((self.host, self.port), APIHandler)
        self.running = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        
        logger.info(f"API server started on http://{self.host}:{self.port}")
        print(f"🚀 API server running on http://{self.host}:{self.port}")
        print(f"📚 API Endpoints:")
        print(f"   GET  /api/health")
        print(f"   GET  /api/posts")
        print(f"   POST /api/posts")
        print(f"   POST /api/posts/schedule")
        print(f"   PUT  /api/posts/{{id}}")
        print(f"   DELETE /api/posts/{{id}}")
        print(f"   GET  /api/analytics")
        print(f"   GET  /api/accounts")
        print(f"   POST /api/webhooks")
    
    def stop(self):
        """Stop API server"""
        if self.running and self.server:
            self.server.shutdown()
            self.running = False
            logger.info("API server stopped")


# Global API server instance
api_server_instance = None

def get_api_server(host="localhost", port=8000):
    """Get or create API server instance"""
    global api_server_instance
    if api_server_instance is None:
        api_server_instance = APIServer(host, port)
    return api_server_instance


if __name__ == "__main__":
    # Test server
    server = get_api_server()
    server.start()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        server.stop()
