import aiopg.sa


async def pg_context(app):
    conf = app['config']['postgres']
    engine = await aiopg.sa.create_engine(**conf)
    app['db'] = engine

    yield

    app['db'].close()
    await app['db'].wait_closed()
