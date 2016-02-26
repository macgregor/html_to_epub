from ebooklib import epub
from lib.book import Book
from lib.chapter import Chapter                     #need to import for pickle to work properly
from lib.table_of_contents import TableOfContents   #need to import for pickle to work properly
from lib.config import Config
import optparse, os, traceback, shutil
        
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-c', '--clear-cache', dest='clear', default = False, action = 'store_true', help='Set to download a local copy of the website, clears local cache if it exists')
    parser.add_option('--config', dest='config', help='yaml config file')
    (options, args) = parser.parse_args()

    config = Config(options.config)

    if options.clear and os.path.exists(config.cache):
        shutil.rmtree(config.cache)

    os.makedirs(config.cache, exist_ok=True)

    book = Book(config)
    book.load_html()

    try:
        # write to the file
        epub.write_epub(config.book.epub_filename, book.generate_epub(), {})
    except Exception as e:
        print(traceback.format_exc())
