from app.routes import auth, main

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


def create_app() -> Sanic:
    app = Sanic("payment-app")
    app.register_listener(setup_db, "after_server_start")
    app.blueprint(main)
    app.blueprint(auth, url_prefix="/auth")
    return app
