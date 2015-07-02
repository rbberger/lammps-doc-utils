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

def detect_and_add_command_to_index(content):
    command_pattern = re.compile(r"^(?P<command>.+) command\s*\n")
    m = command_pattern.match(content)

    if m:
        cmd = m.group('command')
        index = ".. index:: %s\n\n" % cmd
        return index + content

    return content

def filter_file_header_until_first_horizontal_line(content):
    hr = '----------\n\n'
    first_hr = content.find(hr)

    if first_hr >= 0:
        return content[first_hr+len(hr):].lstrip()
    return content

def filter_multiple_horizontal_rules(content):
    return re.sub(r"----------[\s\n]+----------", '', content)
