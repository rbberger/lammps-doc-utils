import unittest
import tempfile
import io
import os
import txt2html

class TestBasicFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2html = txt2html.Txt2Html()

    def test_empty_string(self):
        self.assertEquals(self.txt2html.convert(""), "<HTML>\n"
                                                     "</HTML>\n")

    def test_single_paragraph(self):
        self.assertEquals(self.txt2html.convert("Hello World!\n"), "<HTML>\n"
                                                                   "<P>Hello World!\n"
                                                                   "</P>\n"
                                                                   "</HTML>\n")

    def test_two_paragraphs(self):
        s = self.txt2html.convert("Hello World!\n\nBye World!\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello World!\n"
                             "</P>\n"
                             "<P>Bye World!\n"
                             "</P>\n"
                             "</HTML>\n")

    def test_line_concat(self):
        s = self.txt2html.convert("Hello World!\\\nBye World!\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello World!Bye World!\n"
                             "</P>\n"
                             "</HTML>\n")

    def test_html_pass_through(self):
        s = self.txt2html.convert("<div>Raw HTML</div>\n")
        self.assertEquals(s, "<HTML>\n"
                             "<div>Raw HTML</div>\n\n"
                             "</HTML>\n")


class TestMarkup(unittest.TestCase):
    def setUp(self):
        self.markup = txt2html.Markup()
        self.txt2html = txt2html.Txt2Html()

    def test_bold(self):
        self.assertEquals("<B>bold</B>", self.markup.convert("[bold]"))

    def test_italic(self):
        self.assertEquals("<I>italic</I>", self.markup.convert("{italic}"))

    def test_escape_markup(self):
        s = self.markup.convert("[bold] = \\[bold\\]\n"
                                "{italic} = \\{italic\\}\n")
        self.assertEquals("<B>bold</B> = [bold]\n"
                          "<I>italic</I> = {italic}\n", s)

    def test_link_markup(self):
        self.assertEquals("<A HREF = \"link\">Text</A>", self.markup.convert('"Text"_link'))

    def test_multiline_link_markup(self):
        s = self.txt2html.convert('"Te\n'
                                  'xt"_link')
        self.assertEquals("<HTML>\n"
                          "<P><A HREF = \"link\">Te\n"
                          "xt</A>\n"
                          "</P>\n"
                          "</HTML>\n", s)

    def test_ignore_punctuation_in_link(self):
        self.assertEquals("<A HREF = \"link\">Text</A>.", self.markup.convert('"Text"_link.'))
        self.assertEquals("<A HREF = \"link\">Text</A>,", self.markup.convert('"Text"_link,'))
        self.assertEquals("<A HREF = \"link\">Text</A>;", self.markup.convert('"Text"_link;'))
        self.assertEquals("<A HREF = \"link\">Text</A>:", self.markup.convert('"Text"_link:'))
        self.assertEquals("<A HREF = \"link\">Text</A>?", self.markup.convert('"Text"_link?'))
        self.assertEquals("<A HREF = \"link\">Text</A>!", self.markup.convert('"Text"_link!'))
        self.assertEquals("<A HREF = \"link\">Text</A>(", self.markup.convert('"Text"_link('))
        self.assertEquals("<A HREF = \"link\">Text</A>)", self.markup.convert('"Text"_link)'))

    def test_replace_alias_link(self):
        self.markup.add_link_alias("link", "replacement")
        self.assertEquals("<A HREF = \"replacement\">Text</A>", self.markup.convert('"Text"_link'))

class TestFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2html = txt2html.Txt2Html()

    def test_paragraph_formatting(self):
        s = self.txt2html.convert("Hello :p\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello \n"
                             "</P>\n"
                             "</HTML>\n")

    def test_two_paragraphs_through_formatting(self):
        text = "Hello :p\nBye :p\n"
        p = list(self.txt2html.paragraphs(text))
        s = self.txt2html.convert(text)
        self.assertEquals(len(p), 2)
        self.assertEquals(s, "<HTML>\n"
                             "<P>Hello \n"
                             "</P>\n"
                             "<P>Bye \n"
                             "</P>\n"
                             "</HTML>\n")

    def test_break_formatting(self):
        s = self.txt2html.convert("Hello :b\n")
        self.assertEquals(s, "<HTML>\n"
                             "Hello \n"
                             "<BR>\n"
                             "</HTML>\n")

    def test_preformat_formatting(self):
        s = self.txt2html.convert("Hello :pre\n")
        self.assertEquals(s, "<HTML>\n"
                             "<PRE>Hello \n"
                             "</PRE>\n"
                             "</HTML>\n")

    def test_center_formatting(self):
        s = self.txt2html.convert("Hello :c\n")
        self.assertEquals(s, "<HTML>\n"
                             "<CENTER>Hello \n"
                             "</CENTER>\n"
                             "</HTML>\n")

    def test_header_formatting(self):
        s = self.txt2html.convert("Level 1 :h1\n"
                                  "Level 2 :h2\n"
                                  "Level 3 :h3\n"
                                  "Level 4 :h4\n"
                                  "Level 5 :h5\n"
                                  "Level 6 :h6\n")
        self.assertEquals(s, "<HTML>\n"
                             "<H1>Level 1 \n"
                             "</H1>\n"
                             "<H2>Level 2 \n"
                             "</H2>\n"
                             "<H3>Level 3 \n"
                             "</H3>\n"
                             "<H4>Level 4 \n"
                             "</H4>\n"
                             "<H5>Level 5 \n"
                             "</H5>\n"
                             "<H6>Level 6 \n"
                             "</H6>\n"
                             "</HTML>\n")

    def test_all_paragraphs(self):
        s = self.txt2html.convert("one\n"
                                  "two\n"
                                  "three :all(p)\n")
        self.assertEquals("<HTML>\n"
                          "<P>one</P>\n"
                          "<P>two</P>\n"
                          "<P>three </P>\n"
                          "\n"
                          "</HTML>\n", s)

    def test_all_centered(self):
        s = self.txt2html.convert("one\n"
                                  "two\n"
                                  "three :all(c)\n")
        self.assertEquals("<HTML>\n"
                          "<CENTER>one</CENTER>\n"
                          "<CENTER>two</CENTER>\n"
                          "<CENTER>three </CENTER>\n"
                          "\n"
                          "</HTML>\n", s)

    def test_all_breaks(self):
        s = self.txt2html.convert("one\n"
                                  "two\n"
                                  "three :all(b)\n")
        self.assertEquals("<HTML>\n"
                          "one<BR>\n"
                          "two<BR>\n"
                          "three <BR>\n"
                          "\n"
                          "</HTML>\n", s)

    def test_links_with_all_breaks(self):
        s = self.txt2html.convert("\"one\"_link\n"
                                  "\"two\"_link\n"
                                  "\"three\"_link :all(b)\n")
        self.assertEquals("<HTML>\n"
                          "<A HREF = \"link\">one</A><BR>\n"
                          "<A HREF = \"link\">two</A><BR>\n"
                          "<A HREF = \"link\">three</A> <BR>\n"
                          "\n"
                          "</HTML>\n", s)

    def test_all_list_items(self):
        s = self.txt2html.convert("one\n"
                                  "two\n"
                                  "three :all(l)\n")
        self.assertEquals("<HTML>\n"
                          "<LI>one\n"
                          "<LI>two\n"
                          "<LI>three \n"
                          "\n"
                          "</HTML>\n", s)

    def test_two_commands(self):
        s = self.txt2html.convert("one :ulb,l\n")
        self.assertEquals("<HTML>\n"
                          "<UL><LI>one \n"
                          "\n"
                          "</HTML>\n", s)

class TestListFormatting(unittest.TestCase):
    def setUp(self):
        self.txt2html = txt2html.Txt2Html()

    def test_unordered_list(self):
        s = self.txt2html.convert("one\n"
                                  "two\n"
                                  "three :ul\n")
        self.assertEquals(s, "<HTML>\n"
                             "<UL><LI>one\n"
                             "<LI>two\n"
                             "<LI>three \n"
                             "</UL>\n"
                             "</HTML>\n")

    def test_ordered_list(self):
        s = self.txt2html.convert("one\n"
                                  "two\n"
                                  "three :ol\n")
        self.assertEquals(s, "<HTML>\n"
                             "<OL><LI>one\n"
                             "<LI>two\n"
                             "<LI>three \n"
                             "</OL>\n"
                             "</HTML>\n")

    def test_definition_list(self):
        s = self.txt2html.convert("A\n"
                                  "first\n"
                                  "B\n"
                                  "second :dl\n")
        self.assertEquals(s, "<HTML>\n"
                             "<DL><DT>A\n"
                             "<DD>first\n"
                             "<DT>B\n"
                             "<DD>second \n"
                             "</DL>\n"
                             "</HTML>\n")

    def test_list_item(self):
        s = self.txt2html.convert("one :l\n")
        self.assertEquals(s, "<HTML>\n"
                             "<LI>one \n"
                             "\n"
                             "</HTML>\n")

    def test_definition_term(self):
        s = self.txt2html.convert("one :dt\n")
        self.assertEquals(s, "<HTML>\n"
                             "<DT>one \n"
                             "\n"
                             "</HTML>\n")

    def test_definition_description(self):
        s = self.txt2html.convert("one :dd\n")
        self.assertEquals(s, "<HTML>\n"
                             "<DD>one \n"
                             "\n"
                             "</HTML>\n")

    def test_unordered_list_begin(self):
        s = self.txt2html.convert("one :ulb\n")
        self.assertEquals(s, "<HTML>\n"
                             "<UL>one \n"
                             "\n"
                             "</HTML>\n")

    def test_unordered_list_end(self):
        s = self.txt2html.convert("one :ule\n")
        self.assertEquals(s, "<HTML>\n"
                             "one \n"
                             "</UL>\n"
                             "</HTML>\n")

    def test_ordered_list_begin(self):
        s = self.txt2html.convert("one :olb\n")
        self.assertEquals(s, "<HTML>\n"
                             "<OL>one \n"
                             "\n"
                             "</HTML>\n")

    def test_ordered_list_end(self):
        s = self.txt2html.convert("one :ole\n")
        self.assertEquals(s, "<HTML>\n"
                             "one \n"
                             "</OL>\n"
                             "</HTML>\n")

    def test_definition_list_begin(self):
        s = self.txt2html.convert("one :dlb\n")
        self.assertEquals(s, "<HTML>\n"
                             "<DL>one \n"
                             "\n"
                             "</HTML>\n")

    def test_definition_list_end(self):
        s = self.txt2html.convert("one :dle\n")
        self.assertEquals(s, "<HTML>\n"
                             "one \n"
                             "</DL>\n"
                             "</HTML>\n")

class TestSpecialCommands(unittest.TestCase):
    def setUp(self):
        self.txt2html = txt2html.Txt2Html()

    def test_line(self):
        s = self.txt2html.convert("one :line\n")
        self.assertEquals(s, "<HTML>\n"
                             "<HR>one \n"
                             "\n"
                             "</HTML>\n")

    def test_image(self):
        s = self.txt2html.convert("one :image(file)\n")
        self.assertEquals(s, "<HTML>\n"
                             "<IMG SRC = \"file\">one \n"
                             "\n"
                             "</HTML>\n")

    def test_image_with_link(self):
        s = self.txt2html.convert("one :image(file,link)\n")
        self.assertEquals(s, "<HTML>\n"
                             "<A HREF = \"link\"><IMG SRC = \"file\"></A>one \n"
                             "\n"
                             "</HTML>\n")

    def test_named_link(self):
        s = self.txt2html.convert("one :link(name)\n")
        self.assertEquals(s, "<HTML>\n"
                             "<A NAME = \"name\"></A>one \n"
                             "\n"
                             "</HTML>\n")

    def test_define_link_alias(self):
        s = self.txt2html.convert("one :link(alias,value)\n"
                                  "\"test\"_alias")
        self.assertEquals(s, "<HTML>\n"
                             "one \n"
                             "\n"
                             "<P><A HREF = \"value\">test</A>\n"
                             "</P>\n"
                             "</HTML>\n")

    def test_define_link_alias_later(self):
        s = self.txt2html.convert("\"test\"_alias\n\n"
                                  "one :link(alias,value)\n")
        self.assertEquals(s, "<HTML>\n"
                             "<P><A HREF = \"value\">test</A>\n"
                             "</P>\n"
                             "one \n"
                             "\n"
                             "</HTML>\n")

class TestTableCommand(unittest.TestCase):
    def setUp(self):
        self.txt2html = txt2html.Txt2Html()

    def test_single_table_row(self):
        s = self.txt2html.convert("a,b,c :tb")
        self.assertEquals("<HTML>\n"
                          "<DIV ALIGN=center><TABLE  BORDER=1 >\n"
                          "<TR><TD >a</TD><TD >b</TD><TD >c \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "</HTML>\n", s)

    def test_multiple_table_rows(self):
        s = self.txt2html.convert("a,b,c,\nd,e,f,\ng,h,i :tb")
        self.assertEquals("<HTML>\n"
                          "<DIV ALIGN=center><TABLE  BORDER=1 >\n"
                          "<TR><TD >a</TD><TD >b</TD><TD >c</TD><TD ></TD></TR>\n"
                          "<TR><TD >d</TD><TD >e</TD><TD >f</TD><TD ></TD></TR>\n"
                          "<TR><TD >g</TD><TD >h</TD><TD >i \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "</HTML>\n", s)

    def test_fixed_table_columns(self):
        s = self.txt2html.convert("a,b,c,d,\ne,f,g,h :tb(c=3)\n")
        self.assertEquals("<HTML>\n"
                          "<DIV ALIGN=center><TABLE  BORDER=1 >\n"
                          "<TR><TD >a</TD><TD >b</TD><TD >c</TD></TR>\n"
                          "<TR><TD >d</TD><TD >e</TD><TD >f</TD></TR>\n"
                          "<TR><TD >g</TD><TD >h \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "</HTML>\n", s)

    def test_change_cell_separator(self):
        s = self.txt2html.convert("a:b:c :tb(s=:)")
        self.assertEquals("<HTML>\n"
                          "<DIV ALIGN=center><TABLE  BORDER=1 >\n"
                          "<TR><TD >a</TD><TD >b</TD><TD >c \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "</HTML>\n", s)

    def test_change_table_border(self):
        s = self.txt2html.convert("a,b,c :tb(b=0)")
        self.assertEquals("<HTML>\n"
                          "<DIV ALIGN=center><TABLE  BORDER=0 >\n"
                          "<TR><TD >a</TD><TD >b</TD><TD >c \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "</HTML>\n", s)

    def test_change_cell_width(self):
        s = self.txt2html.convert("a,b,c :tb(w=10)")
        self.assertEquals("<HTML>\n"
                          "<DIV ALIGN=center><TABLE  BORDER=1 >\n"
                          "<TR><TD WIDTH=\"10\">a</TD><TD WIDTH=\"10\">b</TD><TD WIDTH=\"10\">c \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "</HTML>\n", s)

    def test_change_table_width(self):
        s = self.txt2html.convert("a,b,c :tb(w=10%)")
        self.assertEquals("<HTML>\n"
                          "<DIV ALIGN=center><TABLE  WIDTH=\"10%\" BORDER=1 >\n"
                          "<TR><TD >a</TD><TD >b</TD><TD >c \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "</HTML>\n", s)

    def test_change_table_alignment(self):
        s = self.txt2html.convert("a :tb(a=l)\n"
                                  "b :tb(a=c)\n"
                                  "c :tb(a=r)\n")
        self.assertEquals("<HTML>\n"
                          "<DIV ALIGN=left><TABLE  BORDER=1 >\n"
                          "<TR><TD >a \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "<DIV ALIGN=center><TABLE  BORDER=1 >\n"
                          "<TR><TD >b \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "<DIV ALIGN=right><TABLE  BORDER=1 >\n"
                          "<TR><TD >c \n"
                          "</TD></TR></TABLE></DIV>\n\n"
                          "</HTML>\n", s)

class TestTxt2HtmlCLI(unittest.TestCase):
    def setUp(self):
        self.out = io.StringIO()
        self.err = io.StringIO()

    def test_convert_single_file(self):
        with tempfile.NamedTemporaryFile(mode='w+t') as f:
            f.write('Hello World!\n')
            f.flush()
            args = [f.name]
            txt2html.main(args=args, out=self.out, err=self.err)
            self.assertEquals("<HTML>\n"
                              "<P>Hello World!\n"
                              "</P>\n"
                              "</HTML>\n", self.out.getvalue())
            self.assertEquals("Converting " + f.name + " ...\n", self.err.getvalue())

    def test_convert_multiple_files(self):
        with tempfile.NamedTemporaryFile(mode='w+t') as f:
            with tempfile.NamedTemporaryFile(mode='w+t') as g:
                f.write('Hello World!\n')
                f.flush()
                g.write('Hello World!\n')
                g.flush()
                args = [f.name, g.name]
                txt2html.main(args=args, out=self.out, err=self.err)
                self.assertEquals("", self.out.getvalue())
                self.assertEquals("Converting " + f.name + " ...\n"
                                  "Converting " + g.name + " ...\n", self.err.getvalue())
                self.assertTrue(os.path.exists(f.name + ".html"))
                self.assertTrue(os.path.exists(g.name + ".html"))
                os.remove(f.name + ".html")
                os.remove(g.name + ".html")

if __name__ == '__main__':
    unittest.main()
