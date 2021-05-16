Codepage Formatter - A formatter to make IBM codepage files parseable with 
python gencodec.py.

Copyright (C) 2021 J. Férard <https://github.com/jferard>

License: GPLv3

# Overview
Unfortunately, when it comes to exotic encodings (I mean: obsolete EBCDIC 
formats), the Python standard library does not provide everything one might 
need.

The IBM website hosts a comprehensive description of codepages at 
ftp://ftp.software.ibm.com/software/globalization/gcoc/attachments/, but
the format is not recognized by the [gencodec.py tool](
https://github.com/python/cpython/blob/main/Tools/unicode/gencodec.py).

Here's a simple script to convert IBM code page files to the format expected
by gencodec.py

# Usage
In most cases, this will be enough:

    cp_formatter = CodepageFormatter()
    cp_formatter.retrieve_description_map()  # read the file description_map.json
    for filename in ("CP01010.txt", "CP01147.txt"):
        cp_formatter.write_codepage_map(filename)

If some character descriptions are unknown, we use the already known encodings 
to generate a map `character description ->
unicode hex representation`.

From command line:

    python3 codepage_formatter.py -u iso-8859-15 CP00923.txt -u cp1140 CP01140.txt CP01010.txt CP01147.txt

Or programmatically:

    cp_formatter = CodepageFormatter()
    cp_formatter.retrieve_description_map()  # read the file description_map.json
    cp_formatter.update_description_map("iso-8859-15", "CP00923.txt")
    cp_formatter.update_description_map("cp1140", "CP01140.txt")
    ... and so on
    cp_formatter.store_description_map()

And then use:

    mkdir cp_py
    cd cp_py
    wget https://raw.githubusercontent.com/python/cpython/main/Tools/unicode/gencodec.py
    python3 -m gencodec ../cp_dest