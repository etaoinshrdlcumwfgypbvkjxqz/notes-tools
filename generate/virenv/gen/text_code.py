import dataclasses as _dataclasses
import enum as _enum
import io as _io
import types as _types
import typing as _typing


@_typing.final
class TextCode:
    __slots__: _typing.ClassVar = ('__blocks', '__by_tag',)
    escapes: _typing.ClassVar[_typing.Collection[str]
                              ] = frozenset({'\\', '{', '}', ': ', })

    @_typing.final
    @_dataclasses.dataclass(init=True,
                            repr=True,
                            eq=True,
                            order=False,
                            unsafe_hash=False,
                            frozen=True,
                            match_args=True,
                            kw_only=False,
                            slots=True,)
    class Block:
        text: str
        _: _dataclasses.KW_ONLY
        tag: str = ''

        @property
        def special(self: _typing.Self) -> bool: return bool(self.tag)

        @property
        def common(self: _typing.Self) -> bool: return not self.special

        def __str__(self: _typing.Self) -> str:
            if self.special:
                return f'{{{self.tag}:{TextCode.escape(self.text)}}}'
            if self.text:
                return TextCode.escape(self.text)
            return '{:}'

    @_typing.final
    @_dataclasses.dataclass(init=True,
                            repr=True,
                            eq=True,
                            order=False,
                            unsafe_hash=False,
                            frozen=True,
                            match_args=True,
                            kw_only=True,
                            slots=True,)
    class ByTagValue:
        idx: int
        block: 'TextCode.Block'

    def __init__(self: _typing.Self, blocks: _typing.Iterable[Block]) -> None:
        self.__blocks: _typing.Sequence[TextCode.Block] = tuple(blocks)
        by_tag: _typing.MutableMapping[str,
                                       _typing.MutableSequence[TextCode.ByTagValue]] = {}
        for idx, block in enumerate(self.__blocks):
            by_tag.setdefault(block.tag, []).append(
                TextCode.ByTagValue(idx=idx, block=block))
        self.__by_tag: _typing.Mapping[str, _typing.Sequence[TextCode.ByTagValue]] = _types.MappingProxyType({
            k: tuple(v) for k, v in by_tag.items()
        })

    def __repr__(self: _typing.Self) -> str:
        return f'{TextCode.Block.__qualname__}(blocks={self.__blocks!r})'

    def __str__(self: _typing.Self) -> str:
        return ''.join(map(str, self.__blocks))

    @property
    def blocks(
        self: _typing.Self) -> _typing.Sequence[Block]: return self.__blocks

    @property
    def by_tag(self: _typing.Self) -> _typing.Mapping[str, _typing.Sequence[ByTagValue]]:
        return self.__by_tag

    @classmethod
    def escape(cls: type[_typing.Self], text: str) -> str:
        def translate(char: str) -> str:
            if char in cls.escapes:
                return f'\\{char}'
            return char
        return ''.join(map(translate, text))

    @staticmethod
    def compiler(code: str) -> _typing.Iterator[Block]:
        @_enum.unique
        class State(_enum.Enum):
            __slots__: _typing.ClassVar = ()

            NORMAL: _typing.ClassVar = _enum.auto()
            ESCAPE: _typing.ClassVar = _enum.auto()
            TAG: _typing.ClassVar = _enum.auto()
            BLOCK: _typing.ClassVar = _enum.auto()
        state: State = State.NORMAL
        stack: _typing.MutableSequence[_io.StringIO | State] = []
        stack.append(_io.StringIO())
        for index, char in enumerate(code + '{}' if not code.endswith('}') or code.endswith('{}') else code):
            if state == State.NORMAL:
                if char == '\\':
                    stack.append(state)
                    state = State.ESCAPE
                elif char == '{':
                    text: _io.StringIO = _typing.cast(_io.StringIO, stack[-1])
                    text0: str = text.getvalue()
                    if text0:
                        yield TextCode.Block(text0)
                        text.seek(0)
                        text.truncate()
                    stack.append(_io.StringIO())
                    state = State.TAG
                elif char == '}':
                    raise ValueError(f'Unexpected char at {index}: {code}')
                else:
                    _typing.cast(_io.StringIO, stack[-1]).write(char)
            elif state == State.ESCAPE:
                prev_state: State = _typing.cast(State, stack.pop())
                _typing.cast(_io.StringIO, stack[-1]).write(char)
                state = prev_state
            elif state == State.TAG:
                if char == '\\':
                    stack.append(state)
                    state = State.ESCAPE
                elif char == '{':
                    raise ValueError(f'Unexpected char at {index}: {code}')
                elif char == ':':
                    stack.append(_io.StringIO())
                    state = State.BLOCK
                elif char == '}':
                    text: _io.StringIO = _typing.cast(
                        _io.StringIO, stack.pop())
                    if text.getvalue():
                        raise ValueError(f'Unexpected char at {index}: {code}')
                    state = State.NORMAL
                else:
                    _typing.cast(_io.StringIO, stack[-1]).write(char)
            elif state == State.BLOCK:
                if char == '\\':
                    stack.append(state)
                    state = State.ESCAPE
                elif char == '{' or char == ':':
                    raise ValueError(f'Unexpected char at {index}: {code}')
                elif char == '}':
                    text: _io.StringIO = _typing.cast(
                        _io.StringIO, stack.pop())
                    tag: _io.StringIO = _typing.cast(_io.StringIO, stack.pop())
                    yield TextCode.Block(text.getvalue(), tag=tag.getvalue())
                    state = State.NORMAL
                else:
                    _typing.cast(_io.StringIO, stack[-1]).write(char)
            else:
                raise ValueError(f'Unexpected state "{state}": {code}')

    @classmethod
    def compile(cls: type[_typing.Self], text: str) -> _typing.Self:
        return cls(cls.compiler(text))
