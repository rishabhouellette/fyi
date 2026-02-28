"""Route registration — includes all APIRouter modules into the FastAPI app."""


def register_routes(app):
    """Import and mount every router on *app*."""
    from routes.api_routes import router as api_router
    from routes.ai_routes import router as ai_router
    from routes.media_routes import router as media_router

    app.include_router(api_router)
    app.include_router(ai_router)
    app.include_router(media_router)
