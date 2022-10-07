import\
    contextlib as _contextlib,\
    datetime as _datetime,\
    io as _io,\
    os as _os,\
    typing as _typing
from .. import globals as _globals


class FileTextLocation:
    __slots__: _typing.Collection[str] = '__file', '__id', '__start', '__end'

    def __init__(self, *, file: str = _os.devnull, id: str = '', **_: _typing.Any):
        self.__file: str = file
        self.__id: str = id
        self.__start: str = f'<!--{_globals.uuid},generate,id,{id}-->'
        self.__end: str = f'<!--{_globals.uuid},generate,end-->'

    def __repr__(self) -> str:
        return f'{type(self).__name__}(file={self.__file!r}, id={self.__id!r})'

    @property
    def file(self) -> str: return self.__file

    @property
    def id(self) -> str: return self.__id

    class FileTextIO(_io.StringIO):
        comment: str = '<!-- Following content is generated at {}. Any edits will be overridden! -->'

        def __init__(self, file: _typing.TextIO, range: slice, **kwargs: _typing.Any) -> None:
            assert file.readable(), file.readable()
            assert file.writable(), file.writable()
            assert range.step is None, range.step

            self.__file: _typing.TextIO = file
            self.__range: slice = range

            file.seek(0)
            file.read(range.start)
            super().__init__(file.read(range.stop - range.start), **kwargs)

        def close(self) -> None:
            try:
                self.seek(0)
                text: str = self.read()
                with self.__file:
                    self.__file.seek(0)
                    all_text: str = self.__file.read()
                    self.__file.seek(0)
                    self.__file.write(
                        ''.join((
                            all_text[:self.__range.start],
                            self.comment.format(
                                _datetime.datetime.now().astimezone().isoformat()),
                            text,
                            all_text[self.__range.stop:]
                        )))
                    self.__file.truncate()
            finally:
                super().close()

    @_contextlib.contextmanager
    def open(self) -> _typing.Iterator[_typing.TextIO]:
        file: _typing.TextIO = open(
            self.__file, mode='r+t', **_globals.open_default_options)
        if not self.__id:
            with file:
                yield file
            return
        try:
            text: str = file.read()
            start: int = text.find(self.__start)
            if start == -1:
                raise ValueError(f'File text location not found: {self}')
            start += len(self.__start)
            end: int = text.find(self.__end, start)
            if end == -1:
                raise ValueError(
                    f'Unenclosed file text location at char {start}: {self}')
            ret: _typing.TextIO = self.FileTextIO(file, slice(start, end))
        except BaseException as exc:
            file.close()
            raise exc
        with ret:
            yield ret
