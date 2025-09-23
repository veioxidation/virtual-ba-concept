import asyncio
import inspect
from typing import Any

import pytest


def _resolve_fixture_kwargs(fixturedef: pytest.FixtureDef[Any], request: pytest.FixtureRequest) -> dict[str, Any]:
    return {name: request.getfixturevalue(name) for name in fixturedef.argnames}


@pytest.hookimpl(tryfirst=True)
def pytest_fixture_setup(fixturedef: pytest.FixtureDef[Any], request: pytest.FixtureRequest):
    func = fixturedef.func
    if inspect.isasyncgenfunction(func):
        kwargs = _resolve_fixture_kwargs(fixturedef, request)
        agen = func(**kwargs)
        value = asyncio.run(agen.__anext__())

        def _finalizer() -> None:
            try:
                asyncio.run(agen.__anext__())
            except StopAsyncIteration:
                pass

        request.addfinalizer(_finalizer)
        return value

    if inspect.iscoroutinefunction(func):
        kwargs = _resolve_fixture_kwargs(fixturedef, request)
        return asyncio.run(func(**kwargs))

    return None


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    if inspect.iscoroutinefunction(pyfuncitem.obj):
        asyncio.run(pyfuncitem.obj(**pyfuncitem.funcargs))
        return True
    return None


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
