from ebooklib import epub
from lxml.etree import tostring
from lib.book import Book
from lib.config import Config
import optparse, os, traceback, shutil
        
def chapter_text_callback(matches):
    paragraphs = []
    for p in matches:
        if len(p.cssselect('a')) == 0:
            paragraphs.append(tostring(p, encoding='unicode'))
    return paragraphs

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-c', '--clear-cache', dest='clear', default = False, action = 'store_true', help='Set to download a local copy of the website, clears local cache if it exists')
    parser.add_option('--config', dest='config', help='yaml config file')
    parser.add_option('-d', '--debug', dest='debug', default=False, action='store_true', help='enable debug output')
    (options, args) = parser.parse_args()

    config = Config(options.config)

    if options.clear and os.path.exists(config.cache):
        shutil.rmtree(config.cache)

    os.makedirs(config.cache, exist_ok=True)

    book = Book(config, options.debug)
    book.load_html()

    try:
        epub.write_epub(config.book.epub_filename, book.generate_epub(chapter_text_callback), {})
    except Exception as e:
        print(traceback.format_exc())
