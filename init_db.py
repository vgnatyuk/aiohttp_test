from sqlalchemy import create_engine, MetaData

from aiohttp_polls.settings import config
from aiohttp_polls.db import currency

DSN = "postgresql://{user}:{password}@{host}:{port}/{database}"


def create_tables(engine):
    meta = MetaData()
    meta.create_all(bind=engine, tables=[currency])


def sample_data(engine):
    conn = engine.connect()
    conn.execute(currency.insert(), [
        {'currency': 'USD', 'USD': 1, 'GBP': 0.701, 'EUR': 0.825, 'RUR': 72.234},
        {'currency': 'GBP', 'USD': 1.409, 'GBP': 1, 'EUR': 1.163, 'RUR': 101.734},
        {'currency': 'EUR', 'USD': 1.112, 'GBP': 0.860, 'EUR': 1, 'RUR': 87.494},
        {'currency': 'RUR', 'USD': 0.014, 'GBP': 0.010, 'EUR': 0.011, 'RUR': 1},
    ])
    conn.close()


if __name__ == '__main__':
    db_url = DSN.format(**config['postgres'])
    engine = create_engine(db_url)

    create_tables(engine)
    sample_data(engine)
