import asyncio

async def sleep(ms):
    await asyncio.sleep(ms / 1000)

def create_task():
    task = {
        'done': False,
    }

    async def cancel(err):
        if not task['done']:
            task['done'] = True
            raise err

    async def finish(result):
        if not task['done']:
            task['done'] = True
            return result

    task['promise'] = asyncio.ensure_future(task['finish'](None))
    task['cancel'] = cancel
    task['finish'] = finish

    return task

def create_done_task():
    task = {
        'done': True,
        'promise': asyncio.ensure_future(asyncio.sleep(0)),
        'cancel': lambda _: None,
        'finish': lambda _: None,
    }
    return task

async def once_with_cleanup(emitter, event, timeout=0, check_condition=None):
    task = create_task()

    async def on_event(*data):
        if callable(check_condition) and not check_condition(*data):
            return

        await task['finish'](data)

    emitter.add_listener(event, on_event)

    if isinstance(timeout, int) and timeout > 0:
        async def timeout_handler():
            if not task['done']:
                await task['cancel'](TimeoutError(f"Event {event} did not fire within timeout of {timeout}ms"))

        asyncio.ensure_future(asyncio.sleep(timeout / 1000)).add_done_callback(lambda _: asyncio.ensure_future(timeout_handler()))

    try:
        return await task['promise']
    finally:
        emitter.remove_listener(event, on_event)

async def with_timeout(promise, timeout):
    async def timeout_handler():
        raise TimeoutError('Promise timed out.')

    return await asyncio.wait_for(asyncio.gather(promise), timeout / 1000, timeout_handler=timeout_handler)
