from app.admin_routes import admin_bp
from app.routes import auth, main
from app.utils import fetch_user_middleware
from app.webhook import webhook

from config import load_environ

from database.engine import engine
from database.models import Base

from sanic import Sanic

from sqlalchemy.ext.asyncio import async_sessionmaker


async def setup_db(app):
    load_environ()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.ctx.session = async_sessionmaker(bind=engine)


def create_app(app_name: str = "payment-app") -> Sanic:
    app = Sanic(app_name)
    app.register_listener(setup_db, "after_server_start")
    app.blueprint([main, auth, admin_bp, webhook])
    app.register_middleware(fetch_user_middleware, "request")
    return app
