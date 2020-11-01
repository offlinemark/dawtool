"""
Parser + emitter for cue files.

rekordbox generated cue files incorrectly specify the time, so this will
correct for it if re-emitting a rekordbox cue file.
"""

from ..project import Project
from ..marker import Marker

import os.path
import io
from dataclasses import dataclass


@dataclass
class CueRawMarker(Marker):
    performer: str
    title: str
    index_num: int
    orig_index: str
    file: str
    file_type: str

    @property
    def recomputed_index(self):
        """
        Recompute index from the time. This is needed for CueRawMarker's from
        rekordbox where the orig_index is incorrect and shouldn't be reused
        when emitting. In this case we never had frame info, so we use 00.
        """
        min, sec = divmod(self.time, 60)
        return '{:02}:{:02}:00'.format(min, sec)


class CueFile(Project):
    EXT = '.cue'

    def __init__(self, filename, stream):
        super().__init__(filename, stream)
        self.contents = stream.read().decode()
        self.performer = 'UNKNOWN'
        self.title = 'UNKNOWN'
        self.path = None
        self.file = None
        self.file_type = None

        # looking for a line like this: REM RECORDED_BY "rekordbox-dj"
        self._from_rekordbox = 'RECORDED_BY "rekordbox-dj"' in self.contents

    def emit(self):
        """
        Should be called after .parse()
        """
        s = io.StringIO()
        s.write(f'PERFORMER "{self.performer}"\n')
        s.write(f'TITLE "{self.title}"\n')
        s.write(f'FILE "{self.file}" {self.file_type}\n')
        for i, m in enumerate(self.markers, start=1):
            s.write(f'  TRACK {i:02} AUDIO\n')

            # guaranteed to have INDEX, but we don't assume anything else
            if m.performer is not None:
                s.write(f'    PERFORMER "{m.performer}"\n')
            if m.title is not None:
                s.write(f'    TITLE "{m.title}"\n')
            if self._from_rekordbox:
                # if from recordbox, we need to compute a proper index, since
                # theirs is wrong
                s.write('    INDEX {:02} {}\n'.format(m.index_num, m.recomputed_index))
            else:
                # safe to directly use the index from the original file
                s.write(f'    INDEX {m.index_num:02} {m.orig_index}\n')
        return s.getvalue()

    def parse(self):
        header, *track_chunks = self.contents.split('TRACK')

        self._parse_header(header)

        # discard header info
        for chunk in track_chunks:
            self.markers.append(self._parse_chunk(chunk))

    def _parse_header(self, header):
        headerlines = header.splitlines()
        self.performer = self._get_line_data('PERFORMER', headerlines) or 'UNKNOWN'
        self.title = self._get_line_data('TITLE', headerlines) or 'UNKNOWN'
        self.file, self.file_type = self._get_line_data('FILE', headerlines) or (None, None)


    def _parse_chunk(self, chunk):
        lines = [x.strip() for x in chunk.splitlines()]

        performer = self._get_line_data('PERFORMER', lines)
        title = self._get_line_data('TITLE', lines)
        path, typ = self._get_line_data('FILE', lines) or (None, None)
        text = None

        # TODO: make this more hardened. what if there is no FILE?
        # what if there is no title/etc?

        # If we have both the performer and track, use them.
        # Otherwise, just use the filename w/o extension and maybe we'll
        # get lucky that the filename looks like "performer - track.mp3"
        if performer is not None and title is not None:
            text = f'{performer} - {title}'
        elif title is not None:
            text = title
        elif performer is not None:
            text = performer
        elif path is not None:
            # TODO: this might be overcomplicated, maybe just use TITLE
            fname = os.path.basename(path)
            fname_no_ext = os.path.splitext(fname)[0]
            text = fname_no_ext
        else:
            # No performer, no title, no file... we have nothing
            text = 'Unknown'

        num, index = self._get_line_data('INDEX', lines) or (None, None)
        return CueRawMarker(self._parse_index(index), text,
                performer,
                title,
                num,
                index,
                path,
                typ
                )

    def _get_line_data(self, key, lines):
        lines = [x for x in lines if x.startswith(key)]
        if not lines:
            return None

        if len(lines) > 1:
            # FIXME: cue files can have multiple INDEX commands with different
            # index "numbers" (0, 1, 2) in one track block. We should be
            # looking for the one with number, which is what we support,
            # but instead we raise this ValueError
            raise ValueError('Multiple lines found with key', key)

        # there should only be 1 per track chunk..
        line = lines[0]

        if key == 'INDEX':
            num, index = line.split()[1:]
            num = int(num)
            if num != 1:
                # see https://www.gnu.org/software/ccd2cue/manual/html_node/INDEX-_0028CUE-Command_0029.html#INDEX-_0028CUE-Command_0029
                raise ValueError('Unimplemented INDEX number', num)
            return num, index
        elif key in ('PERFORMER', 'TITLE'):
            return line.split('"')[1]
        elif key == 'FILE':
            return tuple(map(lambda x: x.strip(), line.split('"')[1:]))
        
        raise ValueError('Unimplemented key', key)

    def _parse_index(self, index):
        """
        Return 0 if index is none
        """
        if index is None:
            return 0
        if self._from_rekordbox:
            return self._parse_index_rekordbox(index)
        else:
            return self._parse_index_std(index)

    @staticmethod
    def _parse_index_rekordbox(index):
        # rekordbox emits non-spec .cue files... instead of mm:ss:ff
        # it seems to do hh:mm:ss
        try:
            hr, min, sec = map(int, index.split(':'))
        except ValueError:
            raise ValueError('Malformed cue index')
        return hr*3600 + min*60 + sec

    @staticmethod
    def _parse_index_std(index):
        try:
            min, sec, frames = map(int, index.split(':'))
        except ValueError:
            raise ValueError('Malformed cue index')
        # ignore frames.. no idea what the frame rate is
        return min*60 + sec
