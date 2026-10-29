"""Atomically replace one PDF page with a same-size static movie poster page."""
import argparse
import os
from pathlib import Path
import tempfile


def replace_page(source, poster, output, page=2):
    from pypdf import PdfReader, PdfWriter
    source, poster, output = map(Path, (source, poster, output))
    if output.is_symlink():
        raise ValueError('unsafe_pdf_output')
    # Close all input handles before Windows replaces an existing output.
    import io
    original = PdfReader(io.BytesIO(source.read_bytes()))
    replacement = PdfReader(io.BytesIO(poster.read_bytes()))
    if type(page) is not int or not 1 <= page <= len(original.pages) or len(replacement.pages) != 1:
        raise ValueError('invalid_static_poster_page')
    old = original.pages[page - 1]
    new = replacement.pages[0]
    if any(abs(float(a) - float(b)) > .1 for a, b in zip(old.mediabox, new.mediabox)):
        raise ValueError('static_poster_size_mismatch')
    writer = PdfWriter()
    for index, item in enumerate(original.pages, 1):
        writer.add_page(new if index == page else item)
    writer.add_metadata({'/Title': 'AI Security Framework Finals', '/Author': ''})
    descriptor, filename = tempfile.mkstemp(prefix='.poster-pdf-', suffix='.tmp', dir=output.parent)
    os.close(descriptor)
    temporary = Path(filename)
    try:
        with temporary.open('wb') as stream:
            writer.write(stream)
        check = PdfReader(temporary)
        if len(check.pages) != len(original.pages):
            raise ValueError('static_poster_page_count_changed')
        # File handle from PdfReader must be closed for replacement on Windows.
        check.close()
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return len(original.pages)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('source', 'poster', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--page', type=int, default=2)
    args = parser.parse_args()
    print('Static PDF movie poster restored; pages:', replace_page(**vars(args)))
