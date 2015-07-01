import re

def detect_local_toc(paragraph):
    local_toc_pattern = re.compile(r"[0-9]+\.[0-9]*\s+.+<BR>", re.MULTILINE)

    m = local_toc_pattern.match(paragraph)

    if m:
        return ""

    return paragraph

def indent(content):
    indented = ""
    for line in content.splitlines():
        indented += "   %s\n" % line
    return indented

def detect_and_format_notes(paragraph):
    note_pattern = re.compile(r"(?P<type>(IMPORTANT )?NOTE):\s+(?P<content>.+)", re.MULTILINE | re.DOTALL)

    if note_pattern.match(paragraph):
        m = note_pattern.match(paragraph)
        content = m.group('content')
        content = indent(content.strip())

        if m.group('type') == 'IMPORTANT NOTE':
            paragraph = '.. warning::\n\n' + content + '\n'
        else:
            paragraph = '.. note::\n\n' + content + '\n'
    return paragraph
