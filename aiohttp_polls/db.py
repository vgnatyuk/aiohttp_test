import aiopg
from aiopg import sa
from sqlalchemy import (
    MetaData, Table, Column, ForeignKey,
    Integer, String, Date, Float
)

meta = MetaData()


currency = Table(
    'currency', meta,

    Column('currency', String(10), nullable=True, primary_key=True),
    Column('USD', Float, nullable=True),
    Column('GBP', Float, nullable=True),
    Column('EUR', Float, nullable=True),
    Column('RUR', Float, nullable=True),

)


async def init_pg(app):
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
    )
    app['db'] = engine


async def close_pg(app):
    app['db'].close()
    await app['db'].wait_closed()
