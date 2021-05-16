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
import argparse
import json
import logging
import re
import urllib.request
from pathlib import Path

GCOC_ATTACHMENTS = ("ftp://ftp.software.ibm.com/software/"
                    "globalization/gcoc/attachments/")


class CodepageFormatter:
    def __init__(self, description_map_filename="description_map.json",
                 cp_source_dir="cp_source", cp_dest_dir="cp_dest",
                 url=GCOC_ATTACHMENTS):
        self.description_map_filename = description_map_filename
        self.cp_source_dir = cp_source_dir
        self.cp_dest_dir = cp_dest_dir
        self.url = url
        logging.debug("description_map_filename: %s", description_map_filename)
        logging.debug("cp_source_dir: %s", cp_source_dir)
        logging.debug("cp_dest_dir: %s", cp_dest_dir)
        logging.debug("url: %s", url)
        self.data = {'filenames': [], 'unicode_by_description': {}}

    def retrieve_description_map(self):
        try:
            with Path(self.description_map_filename
                      ).open("r", encoding="utf-8") as s:
                self.data = json.load(s)
            logging.debug("description_map `%s` parsed",
                          self.description_map_filename)
        except IOError as e:
            logging.exception("description_map `%s` couldn't be parsed",
                              self.description_map_filename)
            pass

    def update_description_map(self, encoding, filename):
        if encoding in self.data['encodings']:
            logging.debug("encoding `%s` already in in description map",
                          encoding)
        else:
            logging.debug("encoding `%s` not found in description map",
                          encoding)
            self.data['encodings'].append(encoding)
            self.data['unicode_by_description'].update(
                self._get_unicode_by_description(encoding, filename))
            logging.debug(
                "encoding `%s` added to description map using filename `%s`",
                encoding, filename)

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

    def store_description_map(self):
        with Path(self.description_map_filename
                  ).open("w", encoding="utf-8") as s:
            json.dump(self.data, s)
        logging.debug("description_map `%s` stored",
                      self.description_map_filename)

    def write_codepage_map(self, filename):
        """

        :param filename:
        :raise ValueError: if a description is not known
        """
        logging.debug("write codepage map for file `%s`",
                      filename)
        unicode_by_description = self.data['unicode_by_description']
        Path(self.cp_dest_dir).mkdir(exist_ok=True)
        dest_path = Path(self.cp_dest_dir, filename)
        with dest_path.open("w", encoding="utf-8") as d:
            gen = self._parse_ibm_file(filename)
            _code_page = next(gen)
            for hex_number, description in gen:
                d.write("{}\t{}\t# {}\n".format(
                    hex_number, unicode_by_description[description],
                    description.upper()))
        logging.debug("write codepage map for file `%s` written: `%s`",
                      filename, dest_path)

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
        source_path = Path(self.cp_source_dir, filename)
        try:
            with source_path.open("rb") as s:
                data = s.read()
            logging.debug("IBM codepage file found: `%s`", source_path)
        except IOError:
            url_filename = self.url + filename
            with urllib.request.urlopen(url_filename) as s:
                data = s.read()
                with source_path.open("wb") as d:
                    d.write(data)
                logging.debug("IBM codepage file `%s` copied to `%s`",
                              url_filename, source_path)

        return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Convert an IBM codepage file to the gencodec.py format')
    parser.add_argument('filename', nargs='+', help='a file to convert')
    parser.add_argument('-d', '--description-map',
                        default='description_map.json',
                        help='a json file that stores descriptions')
    parser.add_argument('-u', '--update', action='append', nargs=2,
                        metavar=('python_encoding', 'IBM_cp_name'),
                        help='update the description map')
    parser.add_argument('--cp-source',
                        default='cp_source',
                        help='the source directory for IBM codepage files')
    parser.add_argument('--cp-dest',
                        default='cp_dest',
                        help='the dest directory for formatted codepage files')
    parser.add_argument("--url", default="ftp://ftp.software.ibm.com/software/"
                                         "globalization/gcoc/attachments/",
                        help='the base url for IBM codepage files')
    parser.add_argument('-v', action='store_true',
                        help='verbose mode')

    args = parser.parse_args()

    if args.v:
        logging.basicConfig(level=logging.DEBUG)

    cp_formatter = CodepageFormatter(
        description_map_filename=args.description_map,
        cp_source_dir=args.cp_source, cp_dest_dir=args.cp_dest, url=args.url)

    cp_formatter.retrieve_description_map()
    for python_encoding, IBM_cp_name in args.update:
        cp_formatter.update_description_map(python_encoding, IBM_cp_name)
    cp_formatter.store_description_map()
    for filename in args.filename:
        cp_formatter.write_codepage_map(filename)
