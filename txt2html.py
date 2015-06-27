# Python port of txt2html by Steve Plimpton (http://www.cs.sandia.gov/cgi-bin/sjplimp/)
# Written by Richard Berger (2014)
import os
import re
import sys
import argparse

#parser = argparse.ArgumentParser(description='converts a text file with simple formatting & markup into HTML.\nformatting & markup specification is given in README')
#parser.add_argument('-b', dest='breakflag', action='store_true',
#                   help='add a page-break comment to end of each HTML file. useful when set of HTML files will be converted to PDF')
#parser.add_argument('-x', metavar='file-to-skip', dest='skip_files', action='append')
#parser.add_argument('--generate-title', dest='create_title', action='store_true', help='add HTML head page title based on first h1,h2,h3,h4... element')
#parser.add_argument('files',  metavar='file', nargs='+', help='one or more files to convert')

#args = parser.parse_args()

agetitle = ""
aliases = {}
listflag = False
allflag = False
tableflag = False  # makes a table if tb command specified
rowquit = 0        # number of cols per row if c=N specified (default = 0)
dwidth = "0"       # width for all of the columns
tabledelim = ""    # specialized separator
tablealign = ""    # alignment for the table as an image
dataalign = ""     # alignment for data in table
rowvalign = ""     # vertical alignment for table

cnum = []          # column IDs  with specified width
cwidth = []        # column widths

acolnum = []       # column IDs with specified alignment
colalign = []      # column alignment

vacolnum = []      # column IDs with specified vertical alignment
colvalign = []     # column vertical alignment

class Markup(object):
    BOLD_START = "["
    BOLD_END = "]"
    ITALIC_START = "{"
    ITALIC_END = "}"
    START_PLACEHOLDER = "<<PLACEHOLDER>>"
    END_PLACEHOLDER = "<</PLACEHOLDER>>"
    PUNCTUATION_CHARACTERS = '.,;:?!()'

    def __init__(self):
        link_regex = r"(?P<text>[^\"]+)\"_(?P<link>[^\s\t\n]+)"
        self.link_pattern = re.compile(link_regex)
        self.aliases = {}

    def convert(self, text):
        text = self.bold(text)
        text = self.italic(text)
        text = self.link(text)
        return text

    def add_link_alias(self, name, href):
        self.aliases[name] = href

    def bold(self, text):
        text = text.replace("\\" + Markup.BOLD_START, Markup.START_PLACEHOLDER)
        text = text.replace("\\" + Markup.BOLD_END, Markup.END_PLACEHOLDER)
        text = text.replace(Markup.BOLD_START, "<B>")
        text = text.replace(Markup.BOLD_END, "</B>")
        text = text.replace(Markup.START_PLACEHOLDER, Markup.BOLD_START)
        text = text.replace(Markup.END_PLACEHOLDER, Markup.BOLD_END)
        return text

    def italic(self, text):
        text = text.replace("\\" + Markup.ITALIC_START, Markup.START_PLACEHOLDER)
        text = text.replace("\\" + Markup.ITALIC_END, Markup.END_PLACEHOLDER)
        text = text.replace(Markup.ITALIC_START, "<I>")
        text = text.replace(Markup.ITALIC_END, "</I>")
        text = text.replace(Markup.START_PLACEHOLDER, Markup.ITALIC_START)
        text = text.replace(Markup.END_PLACEHOLDER, Markup.ITALIC_END)
        return text

    def link(self, text):
        for name, link in self.link_pattern.findall(text):
            link = link.rstrip(Markup.PUNCTUATION_CHARACTERS)

            if link in self.aliases:
                href = self.aliases[link]
            else:
                href = link

            href = "<A HREF = \"" + href + "\">" + name + "</A>"
            text = text.replace('\"%s\"_%s' % (name, link), href)
        return text

class Formatting(object):
    def __init__(self, markup):
        image_regex = r"^image\((?P<file>[^\,]+)(,(?P<link>[^\,]+))?\)"
        named_link_regex = r"^link\((?P<name>[^\,]+)\)"
        define_link_alias_regex = r"^link\((?P<alias>[^\,]+),(?P<value>[^\,]+)\)"
        self.image_pattern = re.compile(image_regex)
        self.named_link_pattern = re.compile(named_link_regex)
        self.define_link_alias_pattern = re.compile(define_link_alias_regex)
        self.markup = markup

    def convert(self, command, paragraph):
        if command == "p":
            return self.paragraph(paragraph)
        elif command == "b":
            return self.linebreak(paragraph)
        elif command == "pre":
            return self.preformat(paragraph)
        elif command == "c":
            return self.center(paragraph)
        elif command == "h1" or command == "h2" or command == "h3" or \
                        command == "h4" or command == "h5" or command == "h6":
            level = int(command[1])
            return self.header(paragraph, level)
        elif command == "ul":
            return self.unordered_list(paragraph)
        elif command == "ol":
            return self.ordered_list(paragraph)
        elif command == "dl":
            return self.definition_list(paragraph)
        elif command == "l":
            return self.list_item(paragraph)
        elif command == "dt":
            return self.definition_term(paragraph)
        elif command == "dd":
            return self.definition_description(paragraph)
        elif command == "ulb":
            return self.unordered_list_begin(paragraph)
        elif command == "ule":
            return self.unordered_list_end(paragraph)
        elif command == "olb":
            return self.ordered_list_begin(paragraph)
        elif command == "ole":
            return self.ordered_list_end(paragraph)
        elif command == "dlb":
            return self.definition_list_begin(paragraph)
        elif command == "dle":
            return self.definition_list_end(paragraph)
        elif command == "all(p)":
            return self.all_paragraphs(paragraph)
        elif command == "all(c)":
            return self.all_centered(paragraph)
        elif command == "all(b)":
            return self.all_breaks(paragraph)
        elif command == "all(l)":
            return self.all_list_items(paragraph)
        elif command == "line":
            return self.horizontal_rule(paragraph)
        elif command.startswith("image"):
            m = self.image_pattern.match(command)
            return self.image(paragraph, file=m.group('file'), link=m.group('link'))
        elif command.startswith("link"):
            m = self.named_link_pattern.match(command)
            if m:
                return self.named_link(paragraph, name=m.group('name'))
            m2 = self.define_link_alias_pattern.match(command)
            if m2:
                return self.define_link_alias(paragraph, alias=m2.group('alias'), value=m2.group('value'))
        return ""

    def paragraph(self, paragraph):
        return "<P>" + paragraph + "</P>"

    def linebreak(self, paragraph):
        return paragraph + "<BR>"

    def preformat(self, paragraph):
        return "<PRE>" + paragraph + "</PRE>"

    def center(self, paragraph):
        return "<CENTER>" + paragraph + "</CENTER>"

    def header(self, paragraph, level):
        return "<H%d>%s</H%d>" % (level, paragraph, level)

    def unordered_list(self, paragraph):
        converted = "<UL>"
        for line in paragraph.splitlines():
            converted += "<LI>" + line + "\n"
        converted += "</UL>"
        return converted

    def ordered_list(self, paragraph):
        converted = "<OL>"
        for line in paragraph.splitlines():
            converted += "<LI>" + line + "\n"
        converted += "</OL>"
        return converted

    def definition_list(self, paragraph):
        converted = "<DL>"
        is_title = True
        for line in paragraph.splitlines():
            if is_title:
                converted += "<DT>" + line + "\n"
            else:
                converted += "<DD>" + line + "\n"

            is_title = not is_title

        converted += "</DL>"
        return converted

    def list_item(self, paragraph):
        return "<LI>" + paragraph

    def definition_term(self, paragraph):
        return "<DT>" + paragraph

    def definition_description(self, paragraph):
        return "<DD>" + paragraph

    def unordered_list_begin(self, paragraph):
        return "<UL>" + paragraph

    def unordered_list_end(self, paragraph):
        return paragraph + "</UL>"

    def ordered_list_begin(self, paragraph):
        return "<OL>" + paragraph

    def ordered_list_end(self, paragraph):
        return paragraph + "</OL>"

    def definition_list_begin(self, paragraph):
        return "<DL>" + paragraph

    def definition_list_end(self, paragraph):
        return paragraph + "</DL>"

    def all_paragraphs(self, paragraph):
        converted = ""
        for line in paragraph.splitlines():
            converted += "<P>" + line + "</P>\n"
        return converted

    def all_centered(self, paragraph):
        converted = ""
        for line in paragraph.splitlines():
            converted += "<CENTER>" + line + "</CENTER>\n"
        return converted

    def all_breaks(self, paragraph):
        converted = ""
        for line in paragraph.splitlines():
            converted += line + "<BR>\n"
        return converted

    def all_list_items(self, paragraph):
        converted = ""
        for line in paragraph.splitlines():
            converted += "<LI>" + line + "\n"
        return converted

    def horizontal_rule(self, paragraph):
        return "<HR>" + paragraph

    def image(self, paragraph, file, link=None):
        converted = "<IMG SRC = \"" + file + "\">"
        if link:
            converted = "<A HREF = \"" + link + "\">" + converted + "</A>"
        return converted + paragraph

    def named_link(self, paragraph, name):
        return "<A NAME = \"" + name + "\"></A>" + paragraph

    def define_link_alias(self, paragraph, alias, value):
        self.markup.add_link_alias(alias, value)
        return paragraph

class Txt2Html(object):
    def __init__(self):
        self.markup = Markup()
        self.format = Formatting(self.markup)

    def convert(self, content):
        converted = "<HTML>\n"

        if len(content) > 0:
            for paragraph in self.paragraphs(content):
                converted += self.convert_paragraph(paragraph)

        converted += "</HTML>\n"
        return converted

    def convert_paragraph(self, paragraph):
        if self.is_raw_html_paragraph(paragraph):
            return paragraph + '\n'

        if self.has_formatting(paragraph):
            paragraph = self.do_formatting(paragraph)
            return self.do_markup(paragraph)

        return "<P>" + self.do_markup(paragraph) + "</P>\n"

    def has_formatting(self, paragraph):
        return self.last_word(paragraph).startswith(":")

    def last_word(self, text):
        return text.split()[-1]

    def do_formatting(self, paragraph):
        format_str = self.last_word(paragraph)
        paragraph = paragraph.replace(format_str, "")
        commands = format_str[1:]
        command_regex = r"(?P<command>[^\(,]+(\([^\)]+\))?),?"
        command_pattern = re.compile(command_regex)

        for command, _ in reversed(command_pattern.findall(commands)):
            paragraph = self.format.convert(command, paragraph)

        return paragraph + '\n'

    def do_markup(self, paragraph):
        return self.markup.convert(paragraph)

    def paragraphs(self, content):
        paragraph = []
        last_line_had_format = False

        for line in self.lines(content):
            if self.is_paragraph_separator(line) or last_line_had_format:
                if len(paragraph) > 0:
                    yield '\n'.join(paragraph) + '\n'

                if self.is_paragraph_separator(line):
                    paragraph = []
                    last_line_had_format = False
                else:
                    paragraph = [line]
                    last_line_had_format = self.has_formatting(line)
            else:
                paragraph.append(line)
                last_line_had_format = self.has_formatting(line)

        if len(paragraph) > 0:
            yield '\n'.join(paragraph) + '\n'

    def is_raw_html_paragraph(self, paragraph):
        return paragraph.startswith('<') and paragraph.endswith('>\n')

    def is_paragraph_separator(self, line):
        return len(line) == 0 or line.isspace()

    def lines(self, content):
        lines = content.splitlines()
        current_line = ""
        i = 0

        while i < len(lines):
            current_line += lines[i]

            if current_line.endswith("\\"):
                current_line = current_line[0:-1]
            else:
                yield current_line
                current_line = ""

            i += 1

# TODO if output file is not writable
#fprintf(stderr,"ERROR: Could not open %s\n",outfile.c_str())
# #exit(1)


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
        output_filename = os.path.splitext(input_filename)[0] + '.html'
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


def process_commands(flag, command_str, body=None):
    """apply commands one after the other to the paragraph"""

    command_regex = r"(?P<cmd>[^ \t\n\(\),\.]+)(\((?P<args>[^\)]+)\))?,?"
    command_pattern = re.compile(command_regex)

    global aliases
    global listflag
    global allflag
    global pagetitle

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
            pre += "<HR>"
        elif command == "p":
            pre += "<P>"
            post = "</P>" + post
        elif command == "pre":
            pre += "<PRE>"
            post = "</PRE>" + post
        elif command == "c":
            pre += "<CENTER>"
            post = "</CENTER>" + post
        elif command == "h1":
            pre += "<H1>"
            post = "</H1>" + post
        elif command == "h2":
            pre += "<H2>"
            post = "</H2>" + post
        elif command == "h3":
            pre += "<H3>"
            post = "</H3>" + post
        elif command == "h4":
            pre += "<H4>"
            post = "</H4>" + post
        elif command == "h5":
            pre += "<H5>"
            post = "</H5>" + post
        elif command == "h6":
            pre += "<H6>"
            post = "</H6>" + post
        elif command == "b":
            post = "<BR>" + post
        elif command == "ulb":
            pre += "<UL>"
        elif command == "ule":
            post = "</UL>" + post
        elif command == "olb":
            pre += "<OL>"
        elif command == "ole":
            post = "</OL>" + post
        elif command == "dlb":
            pre += "<DL>"
        elif command == "dle":
            post = "</DL>" + post
        elif command == "l":
            pre += "<LI>"
        elif command == "dt":
            pre += "<DT>"
        elif command == "dd":
            pre += "<DD>"
        elif command == "ul":
            listflag = command
            pre += "<UL>"
            post = "</UL>" + post
        elif command == "ol":
            listflag = command
            pre += "<OL>"
            post = "</OL>" + post
        elif command == "dl":
            listflag = command
            pre += "<DL>"
            post = "</DL>" + post
        elif command == "link":
            if len(args) == 1:
                pre += "<A NAME = \"" + args[0] + "\"></A>"
        elif command == "image":
            if len(args) == 1:
                pre += "<IMG SRC = \"" + args[0] + "\">"
            elif len(args) == 2:
                pre += "<A HREF = \"" + args[1] + "\"><IMG SRC = \"" + args[0] + "\"></A>"
        elif command == "tb":
            pre, post = table_command(args, pre, post)
        elif command == "all":
            if len(args) == 1:
                allflag = args[0]
        else:
            print("ERROR: Unrecognized command: ", command)
            exit(1)
    return pre, post


def table_command(args, pre, post):
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

    # loop through each tb() arg
    for arg in args:
        if not '=' in arg:
            continue

        tbcommand, value = arg.split('=')
        if tbcommand == "c":
            rowquit = int(value)
        elif tbcommand == "s":
            tabledelim = value
        elif tbcommand == "b":
            tableborder = value
        elif tbcommand == "w":
            if value.endswith("%"):
                width = value
                tw = ' WIDTH="%s"' % width
            else:
                dwidth = value
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
        elif tbcommand[0:2] == "ca":
            canum = int(tbcommand[2:])
            acolnum.append(canum)
            colalign.append(value)
        elif tbcommand[0:3] == "cva":
            cvanum = int(tbcommand[3:])
            vacolnum.append(cvanum)
            colvalign.append(value)
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

    pre += "<DIV ALIGN=" + align + ">"
    pre += "<TABLE "
    pre += tw
    border = " BORDER=" + tableborder + " >\n"
    pre += border
    post = "</TABLE></DIV>\n" + post
    return pre, post


def substitute_bold_and_italics(s):
    """substitute for bold & italic markers
    if preceded by \ char, then leave markers in text"""
    s = s.replace('\[', '__LEFT_BRACKET__')
    s = s.replace('\]', '__RIGHT_BRACKET__')
    s = s.replace('\{', '__LEFT_BRACE__')
    s = s.replace('\}', '__RIGHT_BRACE__')
    s = s.replace('[', '<B>')
    s = s.replace(']', '</B>')
    s = s.replace('{', '<I>')
    s = s.replace('}', '</I>')
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
        else:
            url = link

        href = "<A HREF = \"" + url + "\">" + text + "</A>"
        s = s.replace('\"%s\"_%s' % (text, link), href)
    return s


def substitute_table(s):
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

    for row in rows:
        table += tr_tag

        for col in columns:
            idx = row*len(columns) + col
            if idx < len(data):
                table += td_tag(col)
                table += data[idx]
                table += "</TD>"

        table += "</TR>\n"

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


def substitute(s):
    """perform substitutions within text of paragraph"""
    global tableflag
    global listflag
    global allflag

    s = substitute_bold_and_italics(s)
    s = substitute_links(s)

    if tableflag:
        # format the paragraph as a table
        tableflag = False
        s = substitute_table(s)

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
                marker = "<LI>"

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


def main_old():
    # parse command-line options and args
    # setup list of files to process
    # npair = # of files to process
    # infile = input file names
    global pagetitle
    global aliases

    # loop over files

    for f in args.files:
        if args.skip_files and f in args.skip_files:
            continue

        # clear global variables before processing file
        pagetitle = ""
        aliases = {}
        tableflag = 0
        listflag = ""
        allflag = ""

        # open files & message to screen

        infile, outfile = file_open(0, f)
        print("Converting", f, "...", file=sys.stderr)

        lines = infile.readlines()

        # scan file for link definitions
        #  read file one paragraph at a time
        # process commands, looking only for link definitions
        for paragraph in paragraphs(lines):
            if is_command(paragraph):
                commands = get_command(paragraph)
                body = get_command_body(paragraph)
                process_commands(0, commands, body)

        # close & reopen files
        infile.close()

        infile, outfile = file_open(len(args.files), f)

        # write leading <HTML>
        outfile.write("<HTML>\n")

        if args.create_title and pagetitle != "":
            outfile.write("<HEAD>\n")
            outfile.write("<TITLE>%s</TITLE>\n" % pagetitle)
            outfile.write("</HEAD>\n")

        # process entire file
        # read file one paragraph at a time

        # process commands for each paragraph
        # substitute text for each paragraph
        # write HTML to output file

        for paragraph in paragraphs(lines):

            # delete newlines when line-continuation char at end-of-line
            paragraph = paragraph.replace('\\\n', '')

            stripped = paragraph.strip(' \t\n')

            pre = ""
            post = ""

            if stripped[0] == '<' and stripped[-1] == '>':
                body = paragraph
            elif is_command(paragraph):
                body = get_command_body(paragraph)
                commands = get_command(paragraph)
                pre, post = process_commands(1, commands)
                body = substitute(body)
            else:
                body = paragraph
                commands = "p"
                pre, post = process_commands(1, commands)
                body = substitute(body)

            # uncomment to remove trailing spaces
            #body = re.sub(r'[ ]+$', '', body, flags=re.MULTILINE)

            final = pre + body + post
            outfile.write("%s\n" % final)

        # write trailing </HTML>

        if args.breakflag:
            outfile.write("<!-- PAGE BREAK -->\n")
        outfile.write("</HTML>\n")

        # close files

        infile.close()
        if outfile != sys.stdout:
            outfile.close()

def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    return parser

def main(args=sys.argv[1:], out=sys.stdout, err=sys.stderr):
    parser = get_argument_parser()
    parsed_args = parser.parse_args(args)

    filename = parsed_args.file

    with open(filename, 'r') as f:
        print("Converting", filename, "...", file=err)
        content = f.read()
        converter = Txt2Html()
        result = converter.convert(content)
        print(result, end='', file=out)

if __name__ == "__main__":
    main()
