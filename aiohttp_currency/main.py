import json
from collections import defaultdict

import aioredis
from aiohttp_session import setup as setup_session
from aiohttp_session.redis_storage import RedisStorage
from aiohttp import web

from aiohttp_currency import db
from settings import config
from routes import setup_routes
from db import init_pg, close_pg


async def init_redis(app):
    async with app['db'].acquire() as conn:
        cursor = await conn.execute(db.currency.select())
        records = await cursor.fetchall()
        currencys = [dict(currency) for currency in records]
        redis = app['redis_pool']

        currency_dict = defaultdict(lambda: {})
        for row in currencys:
            for key, value in row.items():
                if key == 'id':
                    continue
                if key == "currency":
                    currency = value
                    continue
                currency_dict[currency][key] = value
        for k, v in currency_dict.items():
            await redis.set(k, json.dumps(v))


async def setup_redis(app):
    pool = await aioredis.create_redis_pool((
        app['config']['redis']['REDIS_HOST'],
        app['config']['redis']['REDIS_PORT']
    ))

    async def close_redis(app):
        pool.close()
        await pool.wait_closed()

    app.on_startup.append(init_redis)
    app.on_cleanup.append(close_redis)
    app['redis_pool'] = pool
    return pool


async def init_app():
    app = web.Application()
    setup_routes(app)
    app['config'] = config

    app.on_startup.append(init_pg)
    app.on_cleanup.append(close_pg)

    redis_pool = await setup_redis(app)
    setup_session(app, RedisStorage(redis_pool))

    return app


def main():
    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
