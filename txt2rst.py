#! /bin/env python
# Converter of LAMMPS documentation format to Sphinx ReStructured Text
# Written by Richard Berger (2014)
import os
import re
import sys
import argparse
import lammps_filters
from txt2html import Markup, Formatting, TxtParser, TxtConverter

class RSTMarkup(Markup):
    def __init__(self):
        super().__init__()

    def bold_start(self):
        return "**"

    def bold_end(self):
        return "**"

    def italic_start(self):
        return "*"

    def italic_end(self):
        return "*"

    def create_link(self, content, href):
        content = content.strip()
        content = content.replace('\n', '')

        if href in self.references:
            return ":ref:`%s <%s>`" % (content, href)
        elif href in self.aliases:
            href = "%s_" % href
        elif href.endswith('.html'):
            href = href[0:-5]
            return ":doc:`%s <%s>`" % (content, href)

        return "`%s <%s>`_" % (content, href)

class RSTFormatting(Formatting):
    RST_HEADER_TYPES = '#*=-^"'

    def __init__(self, markup):
        super().__init__(markup)

    def paragraph(self, content):
        return content.strip() + "\n"

    def linebreak(self, content):
        return content.strip()

    def preformat(self, content):
        return "::\n\n" + self.indent(content.strip())

    def horizontal_rule(self, content):
        return "\n----------\n\n" + content.strip()

    def image(self, content, file, link=None):
        converted = ".. image:: " + file + "\n"
        if link:
            converted += "   :target: " + link + "\n"
        return converted + content.strip()

    def named_link(self, paragraph, name):
        self.markup.add_internal_reference(name)
        return (".. _%s:\n\n" % name) + paragraph

    def define_link_alias(self, paragraph, alias, value):
        self.markup.add_link_alias(alias, value)
        return (".. _%s: %s\n\n" % (alias, value)) + paragraph

    def header(self, content, level):
        header_content = content.strip()
        header_underline = RSTFormatting.RST_HEADER_TYPES[level-1] * len(header_content)
        return header_content + "\n" + header_underline + "\n"

    def unordered_list_item(self, paragraph):
        return "* " + paragraph.strip()

    def ordered_list_item(self, paragraph, index):
        if index is None:
            index = "#"
        return str(index) + ". " + paragraph.strip()

    def definition_term(self, paragraph):
        return paragraph.strip()

    def definition_description(self, paragraph):
        return self.indent(paragraph.strip())

    def unordered_list_begin(self, paragraph):
        return paragraph

    def unordered_list_end(self, paragraph):
        return paragraph

    def ordered_list_begin(self, paragraph):
        if paragraph.startswith('* '):
            paragraph = '#. ' + paragraph[2:]
        return paragraph

    def definition_list_begin(self, paragraph):
        return paragraph

    def definition_list_end(self, paragraph):
        return paragraph

    def ordered_list_end(self, paragraph):
        return paragraph

    def begin_document(self):
        return ""

    def end_document(self):
        return ""

    def raw_html(self, content):
        raw_directive = ".. raw:: html\n\n"
        return raw_directive + self.indent(content)

    def indent(self, content):
        indented = ""
        for line in content.splitlines():
            indented += "   %s\n" % line
        return indented

    def table(self, paragraph, configuration):
        return self.raw_html(super().table(paragraph, configuration))

class Txt2Rst(TxtParser):
    def __init__(self):
        super().__init__()
        self.markup = RSTMarkup()
        self.format = RSTFormatting(self.markup)
        self.register_filters()

    def register_filters(self):
        self.paragraph_filters.append(lammps_filters.detect_local_toc)
        self.paragraph_filters.append(lammps_filters.detect_and_format_notes)

class Context(object):
    def __init__(self):
        self.is_header = False
        self.is_centered = False
        self.is_hlist = False

def file_open(npair, input_filename):
    if not os.path.exists(input_filename):
        alternative_filename = input_filename + '.txt'
        if not os.path.exists(alternative_filename):
            print("ERROR: Could not open ", input_filename, " or ", alternative_filename)
            exit(1)
        else:
            input_filename = alternative_filename

    infile = open(input_filename, 'r')

    if npair == 0:
        return infile, None
    elif npair == 1:
        outfile = sys.stdout
    else:
        output_filename = os.path.splitext(input_filename)[0] + '.rst'
        outfile = open(output_filename, 'w')

    return infile, outfile


def paragraphs(lines, is_separator=str.isspace, joiner=''.join):
    paragraph = []

    for line in lines:
        if is_separator(line):
            if paragraph:
                yield joiner(paragraph)
                paragraph = []
        elif len(line) > 0 and line.split()[-1].startswith(':'):
            paragraph.append(line)
            yield joiner(paragraph)
            paragraph = []
        else:
            paragraph.append(line)

    if paragraph:
        yield joiner(paragraph)


def is_command(paragraph):
    return paragraph.split()[-1].startswith(':')


def get_command(paragraph):
    return paragraph.split()[-1][1:]


def get_command_body(paragraph):
    command = ':' + get_command(paragraph)
    parts = paragraph.rsplit(command, 1)
    return ''.join(parts)


def process_commands(flag, command_str, body, context):
    """apply commands one after the other to the paragraph"""

    command_regex = r"(?P<cmd>[^ \t\n\(\),\.]+)(\((?P<args>[^\)]+)\))?,?"
    command_pattern = re.compile(command_regex)

    global aliases
    global listflag
    global allflag
    global pagetitle
    global ignore_next_paragraph

    indent = 0
    header_types = "=-#*+~"
    header_pattern = re.compile(r"h(?P<level>[0-6])")
    numbered_header_pattern = re.compile(r"^[0-9]+\.[0-9]* ")

    pre = ""
    post = command_pattern.sub('', command_str)  # retain trailing punctuation

    for command, _, args_str in command_pattern.findall(command_str):
        if args_str:
            args = args_str.split(',')
        else:
            args = []

        # if only in scan mode, just operate on link command
        if flag == 0:
            if command == "link" and len(args) == 2:
                if args[0] in aliases:
                    print("ERROR: Link %s appears more than once\n" % args[0])
                    exit(1)

                aliases[args[0]] = args[1]
            elif command[0] == "h" and body and pagetitle == "":
                pagetitle = body.strip()
            else:
                continue

        # process the command
        if command == "line":
            pre += "\n------------\n"
            ignore_next_paragraph = False # found first <HR>
        elif command == "p":
            pre += ""
            post = "\n" + post
        elif command == "pre":
            pre += "::\n\n"
            indent = 1
            post = "\n" + post
        elif command == "c":
            context.is_centered = True
        elif header_pattern.match(command):
            m = header_pattern.match(command)
            level = int(m.group('level'))

            # fixes some mistakes in original documentation
            if (level == 3 or level == 4) and not numbered_header_pattern.match(body):
                level = 5

            post = '\n' + header_types[level-1]*len(body.strip()) + '\n' + post
            context.is_header = True
        elif command == "b":
            post = "<BR>" + post
        elif command == "ulb":
            #pre += "<UL>"
            pass
        elif command == "ule":
            # post = "</UL>" + post
            pass
        elif command == "olb":
            pre += "\n"
        elif command == "ole":
            post = "\n" + post
        elif command == "dlb":
            pre += "\n"
        elif command == "dle":
            post = "\n\n" + post
        elif command == "l":
            pre += "* "
        elif command == "dt":
            post = ":"
        elif command == "dd":
            indent = 1
        elif command == "ul":
            listflag = command
            pre += "\n"
            post = "\n" + post
        elif command == "ol":
            listflag = command
            pre += "\n"
            post = "\n" + post
        elif command == "dl":
            listflag = command
            pre += "\n"
            post = "\n" + post
        elif command == "link":
            if len(args) == 1:
                pre = ".. " + args[0] + ":\n\n" + pre
        elif command == "image":
            if len(args) == 1:
                pre += ".. image:: " + args[0]
            elif len(args) == 2:
                pre += ".. image:: " + args[0] + "\n   :target: " + args[1]

            if context.is_centered:
                pre += "\n   :align: center"

            pre += '\n'
        elif command == "tb":
            pre, post = table_command(args, pre, post, context)
        elif command == "all":
            if len(args) == 1:
                allflag = args[0]
        else:
            print("ERROR: Unrecognized command: ", command)
            exit(1)
    return pre, post, indent


def table_command(args, pre, post, context):
    """read the table command and set settings"""
    global tableflag
    global rowquit
    global tablealign
    global dataalign
    global rowvalign
    global cnum
    global acolnum
    global vacolnum
    global cwidth
    global colalign
    global colvalign
    global tabledelim
    global dwidth

    tableflag = True

    # these are the table defaults
    tableborder = "1"
    rowquit = 0
    tablealign = "c"
    dataalign = "0"
    rowvalign = "0"

    cnum = []
    acolnum = []
    vacolnum = []

    cwidth = []
    colalign = []
    colvalign = []

    tabledelim = ","
    tw = ""
    dwidth = "0"
    context.is_hlist = False

    # loop through each tb() arg
    for arg in args:
        if not '=' in arg:
            continue

        tbcommand, value = arg.split('=')
        if tbcommand == "c":
            rowquit = int(value)
            context.is_hlist = True
        elif tbcommand == "s":
            tabledelim = value
            context.is_hlist = False
        elif tbcommand == "b":
            tableborder = value
        elif tbcommand == "w":
            if value.endswith("%"):
                width = value
                tw = ' WIDTH="%s"' % width
            else:
                dwidth = value
            context.is_hlist = False
        elif tbcommand == "ea":
            dataalign = value
        elif tbcommand == "eva":
            rowvalign = value
        elif tbcommand == "a":
            tablealign = value
        elif tbcommand[0:2] == "cw":
            cwnum = int(tbcommand[2:])
            cnum.append(cwnum)
            cwidth.append(value)
            context.is_hlist = False
        elif tbcommand[0:2] == "ca":
            canum = int(tbcommand[2:])
            acolnum.append(canum)
            colalign.append(value)
            context.is_hlist = False
        elif tbcommand[0:3] == "cva":
            cvanum = int(tbcommand[3:])
            vacolnum.append(cvanum)
            colvalign.append(value)
            context.is_hlist = False
        else:
            print("ERROR: Unrecognized table command", tbcommand)
            exit(1)

    if tablealign == "c":
        align = "center"
    elif tablealign == "r":
        align = "right "
    elif tablealign == "l":
        align = "left  "
    else:
        align = "center"

    if context.is_hlist:
        pre += ".. hlist::\n   :columns: %d\n\n" % rowquit
        post = ""
    else:
        pre += ".. raw:: html\n\n    <div align=" + align + ">"
        pre += "    <table "
        pre += tw
        border = " border=" + tableborder + " >\n"
        pre += border
        post = "    </table></div>\n\n" + post
    return pre, post


def substitute_bold_and_italics(s, context):
    """substitute for bold & italic markers
    if preceded by \ char, then leave markers in text"""

    s = s.replace('\[', '__LEFT_BRACKET__')
    s = s.replace('\]', '__RIGHT_BRACKET__')
    s = s.replace('\{', '__LEFT_BRACE__')
    s = s.replace('\}', '__RIGHT_BRACE__')

    if context.is_header:
        s = re.sub(r'[0-9]+\.[0-9]*\s+', '', s)
        s = s.replace('[', '')
        s = s.replace(']', '')
        s = s.replace('{', '')
        s = s.replace('}', '')
    else:
        s = s.replace('[', '**')
        s = s.replace(']', '**')
        s = s.replace('{', '*')
        s = s.replace('}', '*')

    s = s.replace('__LEFT_BRACKET__', '[')
    s = s.replace('__RIGHT_BRACKET__', ']')
    s = s.replace('__LEFT_BRACE__', '{')
    s = s.replace('__RIGHT_BRACE__', '}')
    return s


def substitute_links(s):
    link_regex = r"(?P<text>[^\"]+)\"_(?P<link>[^\s\t\n]+)"
    link_pattern = re.compile(link_regex)

    # TODO fprintf(stderr,"ERROR: Could not find matching \" for \"_ in %s\n",
    # TODO fprintf(stderr,"ERROR: Could not find end-of-link in %s\n",s.c_str());

    for text, link in link_pattern.findall(s):
        # ignore punctuation at end of link
        link = link.rstrip('.,?!;:()')

        if link in aliases:
            url = aliases[link]
            href = '`%s <%s>`_' % (text, url)
        else:
            url = link

            if url.endswith('.html'):
                href = ":doc:`%s <%s>`" % (text, url[0:-5])
            else:
                href = '`%s <%s>`_' % (text, url)

        s = s.replace('\"%s\"_%s' % (text, link), href)
    return s


def substitute_table(s, context):
    """format the paragraph as a table"""

    # set up <TR> tag
    # alignment for data in rows
    if dataalign != "0":
        if dataalign == "c":
            align = '"center"'
        elif dataalign == "r":
            align = '"right"'
        elif dataalign == "l":
            align = '"left"'
        else:
            print("ERROR: Unrecognized table alignment argument %s for ea=X\n" % dataalign)
            exit(1)
        tbalign = " ALIGN=" + align
    else:
        tbalign = ""

    # set up vertical  alignment for particular columns
    if rowvalign != "0":
        if rowvalign == "t":
            valign = "top"
        elif rowvalign == "m":
            valign = "middle"
        elif rowvalign == "ba":
            valign = "baseline"
        elif rowvalign == "bo":
            valign = "bottom"
        else:
            print("ERROR: Unrecognized table alignment argument %s for eva=X\n" % rowvalign)
            exit(1)
        va = " VALIGN =\"" + valign + "\""
    else:
        va = ""

    # tr_tag is keyword for data in rows

    tr_tag = "<TR" + tbalign + va + ">"

    # declare integers to help with counting and finding position

    if rowquit > 0:
        data = [x.strip() for x in s.split(tabledelim)]
        rows = list(range(int(len(data)/rowquit)+1))
        columns = list(range(rowquit))
    else:
        row_data = [row.split(tabledelim) for row in s.splitlines()]
        num_cols = max([len(col_data) for col_data in row_data])
        data = []

        for col_data in row_data:
            data += col_data
            data += ['']*(num_cols-len(col_data))

        rows = list(range(len(row_data)))
        columns = list(range(num_cols))

    table = ""

    if context.is_hlist:
        for row in rows:
            for col in columns:
                idx = row*len(columns) + col
                if idx < len(data):
                    table += "   * %s\n" % data[idx]
    else:
        for row in rows:
            table += tr_tag

            for col in columns:
                idx = row*len(columns) + col
                if idx < len(data):
                    table += td_tag(col)
                    table += data[idx]
                    table += "</TD>"

            table += "</TR>\n"

        table = apply_indent(1, table)

    return table


def td_tag(currentc):
    """for tables: build <TD> string based on current column"""

    # eacolumn gives the alignment printout of a specific column
    # va gives vertical alignment to a specific column
    # DT is the complete <td> tag, with width and align
    # dw is the width for tables.  It is also the <dt> tag beginning

    # set up alignment for particular columns
    eacolumn = ""

    for counter, halign in enumerate(colalign):
        if acolnum[counter] == currentc:
            if halign == "l":
                align = "left"
            elif halign == "r":
                align = "right"
            elif halign == "c":
                align = "center"
            else:
                print("ERROR: Unrecognized table alignment argument %s for caM=X\n" % halign)
                exit(1)
            eacolumn = " ALIGN =\"" + align + "\""
            break

    # set up vertical  alignment for particular columns
    va = ""

    for counter, valign in enumerate(colvalign):
        if vacolnum[counter] == currentc:
            if valign == "t":
                valign = "top"
            elif valign == "m":
                valign = "middle"
            elif valign == "ba":
                valign = "baseline"
            elif valign == "bo":
                valign = "bottom"
            else:
                print("ERROR: Unrecognized table alignment argument %s for cvaM=X\n" % valign)
                exit(1)
            va = " VALIGN =\"" + valign + "\""
            break

    # put in special width if specified
    # new code
    # if dwidth has not been set, dw is blank
    # if dwidth has been set, dw has that... unless

    if dwidth == "0":
        dw = " "
    else:
        dw = " WIDTH=\"" + dwidth + "\""

    for i, c in enumerate(cnum):
        # if it is the right column, dw = cwidth property
        if c == currentc:
            dw = " WIDTH=\"" + cwidth[i] + "\""

    # is set for all of this particular separator : reset next separator
    return "<TD" + dw + eacolumn + va + ">"


def substitute(s, context):
    """perform substitutions within text of paragraph"""
    global tableflag
    global listflag
    global allflag

    s = substitute_bold_and_italics(s, context)
    s = substitute_links(s)

    if tableflag:
        # format the paragraph as a table
        tableflag = False
        s = substitute_table(s, context)

    if listflag:
        # if listflag is set, put list marker at beginning of every line
        toggle = False
        list_str = ""

        for line in s.splitlines():
            if listflag == "dl" and not toggle:
                marker = "<DT>"
            elif listflag == "dl" and toggle:
                marker = "<DD>"
            else:
                marker = "* "

            list_str += marker + line + '\n'
            toggle = not toggle

        s = list_str
        listflag = None

    # if allflag is set, add markers to every line
    if allflag:
        if allflag == "p":
            marker1 = "<P>"
            marker2 = "</P>"
        elif allflag == "c":
            marker1 = "<CENTER>"
            marker2 = "</CENTER>"
        elif allflag == "b":
            marker1 = ""
            marker2 = "<BR>"
        elif allflag == "l":
            marker1 = "<LI>"
            marker2 = ""
        else:
            marker1 = ""
            marker2 = ""

        all_str = ""

        for line in s.splitlines():
            all_str += marker1 + line + marker2 + '\n'

        s = all_str

        allflag = False
    return s

def apply_indent(indent, body):
    if indent > 0:
        body = '\n'.join(['   '*indent + line for line in body.splitlines()])
    return body

def main():
    # parse command-line options and args
    # setup list of files to process
    # npair = # of files to process
    # infile = input file names
    global pagetitle
    global aliases
    global ignore_next_paragraph

    local_toc_pattern = re.compile(r"[0-9]+\.[0-9]*\s+.+<BR>", re.MULTILINE)
    note_pattern = re.compile(r"(?P<type>(IMPORTANT )?NOTE):\s+(?P<content>.+)", re.MULTILINE | re.DOTALL)
    command_pattern = re.compile(r"^(?P<command>.+) command\s*\n")

    # loop over files

    for f in args.files:
        if args.skip_files and f in args.skip_files:
            continue

        # clear global variables before processing file
        pagetitle = ""
        aliases = {}
        ignore_paragraph = True
        ignore_next_paragraph = True # ignore file headers up to first <HR>
        tableflag = 0
        listflag = ""
        allflag = ""

        # open files & message to screen

        infile, outfile = file_open(0, f)
        print("Converting ", f, "...", file=sys.stderr)

        lines = infile.readlines()

        # scan file for link definitions
        #  read file one paragraph at a time
        # process commands, looking only for link definitions
        for paragraph in paragraphs(lines):
            ctx = Context()
            if is_command(paragraph):
                commands = get_command(paragraph)
                body = get_command_body(paragraph)
                process_commands(0, commands, body, ctx)

        # close & reopen files
        infile.close()

        infile, outfile = file_open(len(args.files), f)

        # process entire file
        # read file one paragraph at a time

        # process commands for each paragraph
        # substitute text for each paragraph
        # write HTML to output file
        outbuffer = ""

        for paragraph in paragraphs(lines):

            # delete newlines when line-continuation char at end-of-line
            paragraph = paragraph.replace('\\\n', '')

            stripped = paragraph.strip(' \t\r\n')
            ctx = Context()

            pre = ""
            post = ""

            if stripped[0] == '<' and stripped[-1] == '>':
                body = stripped
            elif is_command(stripped):
                body = get_command_body(stripped)
                commands = get_command(stripped)
                pre, post, indent = process_commands(1, commands, body, ctx)
                body = substitute(body, ctx)
            else:
                body = stripped
                commands = "p"
                pre, post, indent = process_commands(1, commands, body, ctx)
                body = substitute(body, ctx)


            body = apply_indent(indent, body)
            body.strip()

            # uncomment to remove trailing spaces
            #body = re.sub(r'[ ]+$', '', body, flags=re.MULTILINE)

            final = pre + body + post

            if local_toc_pattern.match(final):
               ignore_paragraph = True

            if note_pattern.match(final):
                m = note_pattern.match(final)
                final = m.group('content')
                final = apply_indent(1, final)

                if m.group('type') == 'IMPORTANT NOTE':
                    final = '.. warning::\n\n' + final + '\n'
                else:
                    final = '.. note::\n\n' + final + '\n'

            if not ignore_paragraph:
                outbuffer += "%s\n" % final

            ignore_paragraph = ignore_next_paragraph

        # final filter
        outbuffer = re.sub(r"------------[\s\n]+------------", '', outbuffer)

        m = command_pattern.match(outbuffer)

        if m:
            cmd = m.group('command')
            index = ".. index:: %s\n\n" % cmd
            outbuffer = index + outbuffer

        outfile.write(outbuffer)

        # close files

        infile.close()
        if outfile != sys.stdout:
            outfile.close()

class Txt2RstConverter(TxtConverter):
    def get_argument_parser(self):
        parser = argparse.ArgumentParser(description='converts a text file with simple formatting & markup into '
                                                     'Restructured Text for Sphinx.')
        parser.add_argument('-x', metavar='file-to-skip', dest='skip_files', action='append')
        parser.add_argument('files',  metavar='file', nargs='+', help='one or more files to convert')
        return parser

    def create_converter(self, args):
        return Txt2Rst()

    def get_output_filename(self, path):
        filename, ext = os.path.splitext(path)
        return filename + ".rst"

if __name__ == "__main__":
    app = Txt2RstConverter()
    app.run()
