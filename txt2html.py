import os
import re
import sys
import argparse

parser = argparse.ArgumentParser(description='converts a text file with simple formatting & markup into HTML.\nformatting & markup specification is given in README')
parser.add_argument('-b', dest='breakflag', action='store_true',
                   help='add a page-break comment to end of each HTML file. useful when set of HTML files will be converted to PDF')
parser.add_argument('-x', metavar='file-to-skip', dest='skip_files', action='append')
parser.add_argument('files',  metavar='file', nargs='+', help='one or more files to convert')

args = parser.parse_args()


aliases = {}
listflag = False
allflag = False
tableflag = False  # makes a table if tb command specified
rowquit = 0        # number of cols per row if c=N specified (default = 0)
dwidth = 0         # width for all of the columns
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


def process_commands(flag, command_str):
    """apply commands one after the other to the paragraph"""

    command_regex = r"(?P<cmd>[^ \t\n\(\),]+)(\((?P<args>.+)\))?,?"
    command_pattern = re.compile(command_regex)

    global aliases
    global listflag
    global allflag

    pre = ""
    post = ""

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
                #print("Adding alias: ", args[0], args[1])
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
        elif tbcommand[0:1] == "ca":
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
    post = "</TD></TR></TABLE></DIV>\n" + post
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

    currentc = 0 # current column
    nend = 0
    n1 = 0
    n = find_n(s,nend,n1)

    # if there are no separators, go to the end of the string

    if (n < 0) n = s.length()

    # while n exists:

    while True: # n != npos
        # ignore = 0 when pass by \n because looking for delimiters only
        # when ignore==0 do not put in a <tr>
        ignore = 1

        # For each loop starts nend at n
        nend = n

        # current column is 0, (very first loop), insert first <TR>
        if currentc == 0:
            currentc += 1
            DT = td_tag(currentc)
            s.insert(0,tr_tag)
            s.insert(tr_tag.length(),DT)
            nend = nend+tr_tag.length()+DT.length()
            n = find_n(s,nend,n1)
            if n == n1:
                currentc += 1
            else:
                # currentc will remain one if rowquit==0
                if rowquit > 0:
                    s.erase(n,1);
                    n = find_n(s,nend,n1)
                    currentc += 1
        else:
            # if n is separator
            if n == n1:
                s.erase(n,tabledelim.length())
                if currentc == (rowquit+1) and rowquit != 0:
                    s.insert(nend, "</TD></TR>\n")
                    nend = nend+ 11
                    # set current column back to one to start new line
                    currentc = 1
                else:
                    DT = td_tag(currentc)
                    s.insert (nend,"</TD>")
                    nend = nend+5
                    s.insert(nend,DT)
                    nend=nend+DT.length()
                    # add one so current column is updated
                    currentc++
                    n = find_n(s,nend,n1)
            else: # if n is newline character
                s.erase(n,1);
                # if columns == 0 means ARE searching for newlines
                # else erase and ignore insert <tr> later and
                # search for next separator

                if rowquit == 0:
                    s.insert(nend,"</TD></TR>\n")
                    nend=nend+11
                    # set current column back to one to start new line
                    currentc=1
                else:
                    ignore=0
                    n = find_n(s,nend,n1)

            # if we are at the beginning of the row then insert <TR>

            if currentc==1 && ignore:
                DT = td_tag(currentc) # find DT for currentc=1
                s.insert(nend,tr_tag)
                nend=nend+tr_tag.length()
                s.insert(nend,DT)
                n = find_n(s,nend,n1) # search for next separator
                currentc++
    return s


def td_tag(currentc):
    """for tables: build <TD> string (DT) based on current column"""

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
    va = " "

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

    # DT is set for all of this particular separator : reset next separator
    DT = "<TD" + dw + eacolumn + va + ">"
    return DT


def find_n(s, nend, nsep):
    """for tables:
    find the next separator starting at nend(the end of the last .insert)
    if there is either a delim or newline
    decide which is first
    set n = to that position
    nsep is position of the next separator. changes in here.
    """
    nsep = s.find(tabledelim,nend)
    n2 = s.find('\n',nend)
    m = s.length() - 1;
    if nsep >= 0 and n2 >= 0:
        if nsep <= n2:
            n = nsep
        else:
            n = n2
    else:
        if nsep >= 0:
            n = nsep
        else:
            if (n2 < m):
                n = n2
            else:
                n = string::npos
    return n


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


def main():
    # parse command-line options and args
    # setup list of files to process
    # npair = # of files to process
    # infile = input file names
    global aliases

    # loop over files

    for f in args.files:
        if args.skip_files and f in args.skip_files:
            continue

        # clear global variables before processing file
        aliases = {}
        tableflag = 0
        listflag = ""
        allflag = ""

        # open files & message to screen

        infile, outfile = file_open(0, f)
        print("Converting ", f, "...")

        lines = infile.readlines()

        # scan file for link definitions
        #  read file one paragraph at a time
        # process commands, looking only for link definitions
        for paragraph in paragraphs(lines):
            if is_command(paragraph):
                commands = get_command(paragraph)
                process_commands(0, commands)

        # close & reopen files
        infile.close()

        infile, outfile = file_open(len(args.files), f)

        # write leading <HTML>
        outfile.write("<HTML>\n")

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

if __name__ == "__main__":
    main()