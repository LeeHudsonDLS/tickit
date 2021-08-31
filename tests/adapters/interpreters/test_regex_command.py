from typing import Any, AnyStr, AsyncIterable, Awaitable, Callable, Optional, Tuple

import pytest
from mock import MagicMock

from tickit.adapters.interpreters.regex_command import RegexCommand, RegexInterpreter
from tickit.core.adapter import Adapter


@pytest.fixture
def regex_command(regex: AnyStr, func, interrupt: bool, format: Optional[str]):
    return RegexCommand(regex, func, interrupt, format)


@pytest.fixture
def adapter() -> Adapter:
    return MagicMock(Adapter, instance=True)


@pytest.fixture
def async_iterable_command_func() -> Callable[..., AsyncIterable[AnyStr]]:
    async def async_iterable_command(
        adapter: Adapter, *args: Any
    ) -> AsyncIterable[str]:
        yield "TestReply"

    return MagicMock(async_iterable_command)


@pytest.fixture
def async_command_func() -> Callable[..., Awaitable[AnyStr]]:
    async def async_command(adapter: Adapter, *args: Any) -> str:
        return "TestReply"

    return MagicMock(async_command)


@pytest.fixture
def regex_interpreter():
    return RegexInterpreter()


@pytest.mark.parametrize(
    ["regex", "func", "interrupt", "format", "message"],
    [
        (r"TestMessage", None, False, "utf-8", r"UnmatchedMessage".encode("utf-8")),
        (b"\\x01", None, False, None, b"\x02"),
    ],
)
def test_regex_command_parse_unmatched_returns_none(
    regex_command: RegexCommand, message: AnyStr
):
    assert regex_command.parse(message) is None


@pytest.mark.parametrize(
    ["regex", "func", "interrupt", "format", "message", "expected"],
    [
        (r"TestMessage", None, False, "utf-8", r"TestMessage".encode("utf-8"), tuple()),
        (
            r"TestMessage(\d+)",
            None,
            False,
            "utf-8",
            r"TestMessage42".encode("utf-8"),
            ("42",),
        ),
        (b"\\x01", None, False, None, b"\x01", tuple()),
        (b"\\x01(.)", None, False, None, b"\x01\x02", (b"\x02",)),
    ],
)
def test_regex_command_parse_match_returns_args(
    regex_command: RegexCommand, message: AnyStr, expected: Tuple[object]
):
    assert expected == regex_command.parse(message)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["regex", "func", "interrupt", "format", "args"],
    [
        (r"TestMessage", MagicMock(), False, "utf-8", ("a", "b")),
        (r"TestMessage", MagicMock(), False, "utf-8", (1, 2, 3)),
    ],
)
async def test_regex_command_calls_func_with_args(
    regex_command: RegexCommand, args: Tuple[object], adapter: Adapter
):
    await regex_command(adapter, *args)
    regex_command.func.assert_called_once_with(adapter, *args)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["regex", "interrupt", "format"], [(r"TestMessage", False, "utf-8")],
)
async def test_regex_command_returns_iterable_reply(
    regex: str,
    async_iterable_command_func: Callable[..., AsyncIterable[AnyStr]],
    interrupt: bool,
    format: str,
    adapter: Adapter,
):
    regex_command = RegexCommand(regex, async_iterable_command_func, interrupt, format)
    args: Tuple = tuple()
    assert (async_iterable_command_func(adapter), interrupt) == await regex_command(
        adapter, *args
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ["regex", "interrupt", "format"], [(r"TestMessage", False, "utf-8")],
)
async def test_regex_command_wraps_non_iterable_reply(
    regex: str,
    async_command_func: Callable[..., Awaitable[AnyStr]],
    interrupt: bool,
    format: str,
    adapter: Adapter,
):
    regex_command = RegexCommand(regex, async_command_func, interrupt, format)
    args: Tuple = tuple()
    assert (
        await async_command_func(adapter, *args)
        == await (await regex_command(adapter, *args))[0].__anext__()
    )


def test_regex_interpreter_commands_inits_empty(regex_interpreter: RegexInterpreter):
    assert list() == regex_interpreter.commands


def test_regex_interpreter_registers_command(
    regex_interpreter: RegexInterpreter,
    async_command_func: Callable[..., Awaitable[AnyStr]],
):
    regex_interpreter.command(r"TestCommand")(async_command_func)
    assert (
        RegexCommand(r"TestCommand", async_command_func, False, None)
        in regex_interpreter.commands
    )


@pytest.mark.asyncio
async def test_regex_interpreter_handle_returns_command_outputs(
    regex_interpreter: RegexInterpreter,
    async_iterable_command_func: Callable[..., AsyncIterable[AnyStr]],
    adapter: Adapter,
):
    regex_interpreter.command(r"TestCommand", False, "utf-8")(
        async_iterable_command_func
    )
    assert (
        async_iterable_command_func(adapter),
        False,
    ) == await regex_interpreter.handle(adapter, "TestCommand".encode("utf-8"))


@pytest.mark.asyncio
async def test_regex_interpreter_handle_returns_message_for_unknown_command(
    regex_interpreter: RegexInterpreter, adapter: Adapter
):
    assert (
        b"Request does not match any known command"
        == await (
            await regex_interpreter.handle(adapter, "TestCommand".encode("utf-8"))
        )[0].__anext__()
    )
