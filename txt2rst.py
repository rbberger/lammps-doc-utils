#! /bin/env python
# Converter of LAMMPS documentation format to Sphinx ReStructured Text
# Written by Richard Berger (2015)
import os
import re
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

    def center(self, content):
        return content

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

        if "c" in self.current_command_list:
            converted += "   :align: center\n"

        return converted + content.strip()

    def named_link(self, paragraph, name):
        self.markup.add_internal_reference(name)
        return (".. _%s:\n\n" % name) + paragraph

    def define_link_alias(self, paragraph, alias, value):
        self.markup.add_link_alias(alias, value)
        return (".. _%s: %s\n\n" % (alias, value)) + paragraph

    def header(self, content, level):
        header_content = content.strip()
        header_content = re.sub(r'[0-9]+\.[0-9]*\s+', '', header_content)
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

    def get_max_column_widths(self, rows):
        num_columns = max([len(row) for row in rows])
        max_widths = [0] * num_columns

        for columns in rows:
            for col_idx, column in enumerate(columns):
                max_widths[col_idx] = max(max_widths[col_idx], len(column.strip())+2)

        return max_widths

    def create_table_horizontal_line(self, max_widths):
        cell_borders = ['-' * width for width in max_widths]
        return '+' + '+'.join(cell_borders) + "+"

    def table(self, paragraph, configuration):
        paragraph = self.protect_rst_directives(paragraph)

        if configuration['num_columns'] == 0:
            rows = self.create_table_with_columns_based_on_newlines(paragraph, configuration['separator'])
        else:
            rows = self.create_table_with_fixed_number_of_columns(paragraph, configuration['separator'],
                                                                  configuration['num_columns'])

        column_widths = self.get_max_column_widths(rows)
        max_columns = len(column_widths)
        horizontal_line = self.create_table_horizontal_line(column_widths) + "\n"

        tbl = horizontal_line

        for row_idx in range(len(rows)):
            columns = rows[row_idx]

            tbl += "| "
            for col_idx in range(max_columns):
                if col_idx < len(columns):
                    col = columns[col_idx].strip()
                else:
                    col = ""

                tbl += col.ljust(column_widths[col_idx]-2, ' ')
                tbl += " |"

                if col_idx < max_columns - 1:
                    tbl += " "
            tbl += "\n"
            tbl += horizontal_line

        tbl = self.restore_rst_directives(tbl)
        return tbl

    def protect_rst_directives(self, content):
        content = content.replace(":doc:", "0DOC0")
        content = content.replace(":ref:", "0REF0")
        return content

    def restore_rst_directives(self, content):
        content = content.replace("0DOC0", ":doc:")
        content = content.replace("0REF0", ":ref:")
        return content

class Txt2Rst(TxtParser):
    def __init__(self):
        super().__init__()
        self.markup = RSTMarkup()
        self.format = RSTFormatting(self.markup)
        self.register_filters()

    def register_filters(self):
        self.paragraph_filters.append(lammps_filters.detect_local_toc)
        self.paragraph_filters.append(lammps_filters.detect_and_format_notes)
        self.document_filters.append(lammps_filters.filter_file_header_until_first_horizontal_line)
        self.document_filters.append(lammps_filters.detect_and_add_command_to_index)
        self.document_filters.append(lammps_filters.filter_multiple_horizontal_rules)

    def is_ignored_textblock_begin(self, line):
        return line.startswith('.. HTML_ONLY')

    def is_ignored_textblock_end(self, line):
        return line.startswith('.. END_HTML_ONLY')

    def is_raw_textblock_begin(self, line):
        return line.startswith('.. RST')

    def is_raw_textblock_end(self, line):
        return line.startswith('.. END_RST')

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
