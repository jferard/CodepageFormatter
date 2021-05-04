# coding: utf-8
#  Codepage Formatter - A formatter to make IBM codepage files parseable
#                       with python gencodec.py.
#     Copyright (C) 2021 J. Férard <https://github.com/jferard>
#
#  This file is part of Codepage Formatter.
#
#  Codepage Formatter is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Codepage Formatter is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import re
import urllib.request
from pathlib import Path

GCOC_ATTACHMENTS = ("ftp://ftp.software.ibm.com/software/"
                    "globalization/gcoc/attachments/")


class CodepageFormatter:
    def __init__(self, description_map_filename="description_map.json",
                 cp_source_dir="cp_source", cp_dest_dir="cp_dest",
                 url=GCOC_ATTACHMENTS):
        self.cp_dest_dir = cp_dest_dir
        self.cp_source_dir = cp_source_dir
        self.url = url
        self.description_map_filename = description_map_filename
        self.data = {'filenames': [], 'unicode_by_description': {}}

    def retrieve_description_map(self):
        try:
            with Path(self.description_map_filename
                      ).open("r", encoding="utf-8") as s:
                self.data = json.load(s)
        except IOError:
            pass

    def store_description_map(self):
        with Path(self.description_map_filename
                  ).open("w", encoding="utf-8") as s:
            json.dump(self.data, s)

    def update_description_map(self, encoding, filename):
        if encoding not in self.data['filenames']:
            self.data['filenames'].append(encoding)
            self.data['unicode_by_description'].update(
                self._get_unicode_by_description(encoding, filename))

    def _get_unicode_by_description(self, encoding, filename):
        # we use a known encoding
        # to build the data description -> character
        ret = {}
        gen = self._parse_ibm_file(filename)
        _code_page = next(gen)
        for hex_number, description in gen:
            c = bytes([int(hex_number, 16)]).decode(
                encoding)  # we know the char
            unicode = "0x" + "{:04x}".format(ord(c)).upper()
            ret[description] = unicode
        return ret

    def write_codepage_map(self, filename):
        unicode_by_description = self.data['unicode_by_description']
        Path(self.cp_dest_dir).mkdir(exist_ok=True)
        with Path(self.cp_dest_dir, filename).open("w", encoding="utf-8") as d:
            gen = self._parse_ibm_file(filename)
            _code_page = next(gen)
            for hex_number, description in gen:
                d.write("{}\t{}\t# {}\n".format(
                    hex_number, unicode_by_description[description],
                    description.upper()))

    def _parse_ibm_file(self, filename):
        """
        Parse an IBM file and yields number, description.
        :param filename: the short filename, e.g. "CP01252.txt"
        """
        data = self._get_data(filename)
        text = data.decode("ascii")
        for line in text.split("\n"):
            if line.startswith("* Code Page"):
                yield line.split(":")[1].strip()
            elif re.match("^[0-9A-F]{2} .*$", line):
                try:
                    hex_number = "0x" + line[:2]
                    description = line[19:].strip()
                    yield hex_number, description
                except:
                    pass

    def _get_data(self, filename):
        Path(self.cp_source_dir).mkdir(exist_ok=True)
        try:
            with Path(self.cp_source_dir, filename).open("rb") as s:
                data = s.read()
        except IOError:
            with urllib.request.urlopen(self.url + filename) as s:
                data = s.read()
                with Path(self.cp_source_dir, filename).open("wb") as d:
                    d.write(data)
        return data


if __name__ == "__main__":
    cp_formatter = CodepageFormatter()
    cp_formatter.retrieve_description_map()
    cp_formatter.update_description_map("iso-8859-15", "CP00923.txt")
    cp_formatter.update_description_map("cp1140", "CP01140.txt")
    cp_formatter.store_description_map()
    for filename in ("CP01010.txt", "CP01147.txt"):
        cp_formatter.write_codepage_map(filename)
