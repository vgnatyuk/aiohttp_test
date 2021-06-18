import json
from aiohttp import web
import db


async def convert(request):
    redis = request.app['redis_pool']
    from_ = request.query.get('from', None)
    to_ = request.query.get('to', None)
    amount = request.query.get('amount', None)

    if not (from_ and to_ and amount):
        success = False
        result = "incorrect data"
        return web.json_response({'success': success, 'result': result}, status=400)

    if await redis.get(from_):
        exchange_rates = {from_: json.loads((await redis.get(from_)).decode('utf-8'))}
        if not (exchange_rates[from_].get(to_, None)):
            success = False
            result = f"haven't info how to convert from {from_} to {to_}"
        elif from_ == to_:
            success = True
            result = f'{amount} {from_} is {amount} {to_}'
        else:
            success = True
            result = round(exchange_rates[from_][to_] * float(amount), 3)
            result = f'{amount} {from_} is {result} {to_}'
        response = [
            {
                'success': success,
                'result': result,
            }
        ]
        return web.json_response(response, status=200)
    return web.json_response({'success': False, 'result': f"Haven't data about {from_}"}, status=400)


async def database_merge(request):
    merge = request.query.get('merge', None)

    try:
        merge = int(merge)
    except (ValueError, TypeError) as exc:
        result = str(exc)
        return web.json_response({'success': False, 'result': result}, status=400)

    if merge == 1:
        # rewrite
        success, status, result = await rewrite(request)
    elif merge == 0:
        # erase
        success = True
        status = 200
        result = 'erase'
        await erase(request)
    else:
        success = False
        status = 400
        result = "incorrect data"

    response = [
        {
            'success': success,
            'result': result,
        }
    ]
    return web.json_response(response, status=status)


async def erase(request):
    redis = request.app['redis_pool']
    await redis.flushall()

    async with request.app['db'].acquire() as conn:
        await conn.execute(db.currency.delete())


async def rewrite(request):
    from main import init_redis

    currency = request.query.get('currency', None)
    USD = request.query.get('USD', False)
    GBP = request.query.get('GBP', False)
    EUR = request.query.get('EUR', False)
    RUR = request.query.get('RUR', False)

    handlers = {
        'USD': USD,
        'GBP': GBP,
        'EUR': EUR,
        'RUR': RUR,
    }

    async with request.app['db'].acquire() as conn:
        cursor = await conn.execute(db.currency.select().where(db.currency.c.currency == currency))
        records = await cursor.fetchall()
        currencys = [dict(currency) for currency in records]
        if not currencys:
            return False, 400, f"Haven't data about {currency} or missing argument: 'currency'"

        for key in currencys[0].keys():
            if key == 'currency':
                continue
            new_currency_value = handlers[key]
            if new_currency_value is False:
                continue
            elif new_currency_value == 'None':
                currencys[0][key] = None
                continue
            currencys[0][key] = new_currency_value

        update_db = db.currency.update().values({db.currency.c.USD: currencys[0]['USD'],
                                                 db.currency.c.GBP: currencys[0]['GBP'],
                                                 db.currency.c.EUR: currencys[0]['EUR'],
                                                 db.currency.c.RUR: currencys[0]['RUR'],
                                                 }).where(db.currency.c.currency == currencys[0]['currency'])
        await conn.execute(update_db)
        await init_redis(request.app)

        return True, 200, 'rewrite'

