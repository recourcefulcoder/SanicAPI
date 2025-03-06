from app.admin_routes import admin_bp
from app.routes import auth, main
from app.utils import fetch_user_middleware
from app.webhook import webhook

from config import load_environ

from database.engine import engine

from sanic import Sanic

from sqlalchemy.ext.asyncio import async_sessionmaker


async def add_db_session(app):
    load_environ()  # to make sure SANIC_SECRET is stored in app.config
    app.ctx.session = async_sessionmaker(bind=engine)


def create_app(app_name: str = "payment-app") -> Sanic:
    app = Sanic(app_name)
    app.register_listener(add_db_session, "after_server_start")
    app.blueprint([main, auth, admin_bp, webhook])
    app.register_middleware(fetch_user_middleware, "request")
    return app
