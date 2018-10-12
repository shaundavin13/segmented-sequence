import typing as _typing

_Identifier = _typing.Union[str, int]


class SegmentedSequence(object):
    _default_name = 'SegmentedSequence'

    def __init__(
            self,
            data: _typing.List,
            name: str=None,
            segments: _typing.List[str]=None,
            segment_indices:
            _typing.List[int]=None
    ) -> None:
        self.all: _typing.List = data
        self._segment_names: _typing.List[str] = segments or []
        self._segment_indices: _typing.List[int] = segment_indices or [0] * (len(segments or []) + 1)
        self.name: str = name or self._default_name

    def __str__(self) -> str:
        segments: _typing.List = ['{}({})'.format(name, self._get_segment_length(name)) for name in self._segment_names]
        return '<{name} {segments}>'.format(name=self.name, segments=', '.join(segments))

    def __getitem__(self, val: _typing.Union[int, slice]) -> _typing.Any:
        return self.all[val]

    def __getattr__(self, item) -> _typing.Any:
        if item in self._segment_names:
            start: int
            stop: int
            start, stop = self._get_segment_indices(item)
            return self.all[start: stop]
        raise AttributeError

    def _get_segment_length(self, segment_identifier: _Identifier) -> int:
        segment_number: int = self._get_segment_number(segment_identifier)
        return self._segment_indices[segment_number + 1] - self._segment_indices[segment_number]

    def _get_segment_number(self, segment_identifier: _Identifier) -> int:
        if isinstance(segment_identifier, int):
            return segment_identifier
        try:
            return self._segment_names.index(segment_identifier)
        except ValueError:
            raise KeyError('{} does not exist in the sequence'.format(segment_identifier))

    def _get_segment_name(self, segment_number: int) -> str:
        return self._segment_names[segment_number]

    def _get_segment_indices(self, segment_identifier: _Identifier) -> _typing.Tuple:
        segment_number: int = self._get_segment_number(segment_identifier)
        return self._segment_indices[segment_number], self._segment_indices[segment_number + 1]

    def _update_segment_indices(self, index, value) -> None:
        segment_indices: _typing.List = self._segment_indices.copy()
        segment_indices[index] = value
        self._segment_indices: _typing.List = segment_indices

    def _update_segment_start(self, segment_identifier: _Identifier, value: int) -> None:
        segment_number: int = self._get_segment_number(segment_identifier)
        self._update_segment_indices(segment_number, value)

    def _update_last_segment_end(self, value) -> None:
        self._update_segment_indices(len(self._segment_indices) - 1, value)

    def move_segment(self, segment_name: str, new_segment_start: int) -> None:
        segment_start: int
        segment_end: int
        segment_start, segment_end = self._get_segment_indices(segment_name)
        segment_number: int = self._get_segment_number(segment_name)
        try:
            next_segment_name: _typing.Optional[str] = self._get_segment_name(segment_number + 1)
        except IndexError:
            next_segment_name = None

        if new_segment_start > segment_end:
            if next_segment_name is None:
                self._update_last_segment_end(new_segment_start)
            else:
                self.move_segment(next_segment_name, new_segment_start)

        self._update_segment_start(segment_name, new_segment_start)

    def extend_right(self) -> None:
        self._update_last_segment_end(len(self.all))

    def extend_left(self) -> None:
        self._update_segment_indices(0, 0)

    def is_extended_right(self)-> bool:
        return self._segment_indices[-1] == len(self.all)

    def is_extended_left(self) -> bool:
        return self._segment_indices[0] == 0

    def append(self, value) -> None:
        should_extend: bool = self.is_extended_right()
        self.all.append(value)
        if should_extend:
            self.extend_right()

    def appendleft(self, value) -> None:
        should_extend: bool = self.is_extended_left()
        self.all = [value] + self.all
        self._segment_indices = [idx + 1 for idx in self._segment_indices]
        if should_extend:
            self.extend_left()

    def pop(self) -> _typing.Any:
        should_extend: bool = self.is_extended_right()
        rv: _typing.Any = self.all.pop()
        if should_extend:
            self.extend_right()
        return rv

    def popleft(self) -> _typing.Any:
        self._segment_indices = [idx - 1 if idx > 0 else idx for idx in self._segment_indices]
        return self.all.pop(0)

    def to_dict(self) -> _typing.Dict:
        segments: _typing.List[_typing.Dict] = []
        for segment_name in self._segment_names:
            segment: _typing.Dict = dict(name=segment_name, value=getattr(self, segment_name))
            start: int
            end: int
            start, end = self._get_segment_indices(segment_name)
            segment.update({'start': start, 'end': end})
            segments.append(segment)

        result: _typing.Dict = dict(segments=segments, name=self.name)
        result['data'] = self.all
        return result

    @staticmethod
    def from_dict(source: _typing.Dict):
        if 'segments' not in source:
            raise ValueError('Source dictionary must have a key called segments and all')

        segment_indices: _typing.List[int] = []
        segments: _typing.List[_typing.Dict] = source['segments']
        complete_data: _typing.List = []

        for segment_number, segment in enumerate(segments):
            segment_indices.append(segment['start'])
            complete_data.append(segment['value'])

            is_last_segment: bool = segment_number == len(segments) - 1
            if is_last_segment:
                segment_indices.append(segment['end'])

        segment_names: _typing.List[str] = [segment['name'] for segment in segments]
        all: _typing.List = source['data']
        name: str = source.get('name', SegmentedSequence._default_name)

        return SegmentedSequence(all, name=name, segments=segment_names, segment_indices=segment_indices)
