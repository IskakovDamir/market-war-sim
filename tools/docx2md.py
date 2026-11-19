"""Convert a team doc saved as .docx into the markdown extract.py reads (headings as # **...**, tables as | rows |).
usage: python3 docx2md.py <file.docx> > <company>.md     (needs python-docx)"""
import sys, docx
from docx.table import Table
from docx.text.paragraph import Paragraph
def conv(path):
    d = docx.Document(path); out = []
    for el in d.element.body.iterchildren():
        tag = el.tag.split('}')[1]
        if tag == 'p':
            p = Paragraph(el, d); t = p.text.strip()
            if not t: continue
            st = (p.style.name or '').lower()
            if st.startswith('heading 1') or st == 'title': out.append(f'# **{t}**')
            elif st.startswith('heading'): out.append(f'## **{t}**')
            else:
                bold = ''.join(f'**{r.text}**' if r.bold else r.text for r in p.runs)
                out.append(bold)
        elif tag == 'tbl':
            tb = Table(el, d); out.append('')
            for i, row in enumerate(tb.rows):
                cells = []
                for c in row.cells: cells.append(' '.join(x.strip() for x in c.text.split('\n') if x.strip()).replace('|', '/'))
                out.append('| ' + ' | '.join(cells) + ' |')
                if i == 0: out.append('|' + ' :---- |' * len(cells))
            out.append('')
    return '\n'.join(out) + '\n# **END**\n'
if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    print(conv(sys.argv[1]))
