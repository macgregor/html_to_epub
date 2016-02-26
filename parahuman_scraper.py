from ebooklib import epub
from lib.book import Book
from lib.chapter import Chapter
from lib.table_of_contents import TableOfContents
import optparse, os

html_cache_location = './cache/html'
pickle_cache = './cache/parahumans'
        
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-c', '--clear-cache', dest='clear', default = False, action = 'store_true', help='Set to download a local copy of the website, clears local cache if it exists')
    parser.add_option('-a', '--author', dest='author', default='Wildbow', help='Author of ebook')
    parser.add_option('-t', '--title', dest='title', default='Parahumans - Worm', help='Title of ebook')
    parser.add_option('-u', '--url', dest='url', default='https://parahumans.wordpress.com/table-of-contents/', help='URL to the table of contents of the webpage to scrape')
    parser.add_option('-o', '--output', dest='output', default='parahumans.epub', help='Epub file to output')

    (options, args) = parser.parse_args()

    book = None
    os.makedirs(html_cache_location, exist_ok=True)

    if os.path.isfile(pickle_cache):
        book = Book.restore(pickle_cache)

    if options.clear or book is None:
        book = Book(options.url, options.title, options.author, pickle_cache, html_cache_location)
        book.init_html()
        book.cache()

    try:
        # write to the file
        epub.write_epub(options.output, book.generate_epub(), {})
    except Exception as e:
        print(traceback.format_exc())
        book.cache()
