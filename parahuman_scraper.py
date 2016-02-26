import lxml.html
from lxml.cssselect import CSSSelector
from lxml.etree import tostring
from collections import OrderedDict
from urllib.request import urlopen
from urllib import parse
from ebooklib import epub
from tqdm import tqdm
import pickle, uuid, re, os, traceback, optparse

html_cache_location = './cache/html'
pickle_cache = './cache/parahumans'

os.makedirs(html_cache_location, exist_ok=True)

class Chapter:
    title_class = 'entry-title'
    chapter_class = 'entry-content'
    section_regex = '^(\w+)\s*.*$'
    
    def __init__(self, url, cache_location=html_cache_location):
        url = parse.urlsplit(url)
        url = list(url)
        url[2] = parse.quote(url[2])
        url = parse.urlunsplit(url)

        self.cache_location = cache_location
        self.cache_filename = str(uuid.uuid4())+'.html'
        self.url = url
        self.tree = None
        self.title = None
        self.text_markup = None

    def __getstate__(self):
        odict = self.__dict__.copy()
        odict['tree'] = None
        return odict

    def load_dom(self):
        with open(os.path.join(self.cache_location, self.cache_filename), 'r') as f:
            self.tree = lxml.html.fromstring(f.read())

        self.get_title()
        self.get_text()

        return self.tree

    def save_html(self):
        response = urlopen(self.url)
        content = response.read().decode('utf-8', 'ignore')
        response.close()

        with open(os.path.join(self.cache_location, self.cache_filename), 'w') as out:
            out.write(content)
        
    def get_title(self):
        if self.tree is not None:
            sel = CSSSelector('h1.entry-title a, h1.entry-title')
            for t in sel(self.tree):
                self.title = t.text
    
        return self.title

    def get_text(self):
        if self.tree is not None:
            sel = CSSSelector('div.entry-content p')
            match = sel(self.tree)

            paragraphs = []
            for p in match:
                if len(p.cssselect('a')) == 0:
                    paragraphs.append(tostring(p, encoding='unicode').replace('\n', '<br/>'))


            self.text_markup = ''.join(paragraphs)

        return self.text_markup

    def get_epub_section(self):
        return re.match(Chapter.section_regex, self.get_title()).group(1)

    def get_epub_filename(self):
        title = self.get_title()        
        remove = [' ', '#', '\t', ':', ' '] #the last one isnt a normal space...
        for c in remove:
            title = title.replace(c, '_')
        return title + '.xhtml'

    def to_epub(self, css):
        epub_chapter = epub.EpubHtml(title=self.get_title(), file_name=self.get_epub_filename(), lang='hr')
        epub_chapter.content='<html><body><h1>'+self.get_title()+'</h1>'+self.get_text()+'</body></html>'
        epub_chapter.add_item(css)
        return epub_chapter
        
class TableOfContents:
    toc_entry_class = 'entry-content'
    
    def __init__(self, url):
        self.url = url
        self.tree = None
        self.chapters = None

    def __getstate__(self):
        odict = self.__dict__.copy()
        odict['tree'] = None
        return odict       
 
    def load_dom(self):
        response = urlopen(self.url)
        self.tree = lxml.html.fromstring(response.read().decode('utf-8', 'ignore'))
        response.close()

        return self.tree

    def get_chapters(self):
        if self.tree is not None:
            chapters = OrderedDict()
            sel = CSSSelector('div.entry-content a:not([href*="share"])')

            for link in sel(self.tree):
                href = link.get('href')
                if not href.startswith('https://'):
                    href = 'https://' + href

                if href not in chapters:
                    chapters[href] = Chapter(href)
            self.chapters = list(chapters.values())

        return self.chapters

class Book:
    def __init__(self, toc_url, title, author, cache_location=pickle_cache):
        self.cache_location = cache_location
        self.toc = TableOfContents(toc_url)
        self.chapters = None
        self.title = title
        self.author = author

    @classmethod
    def restore(cls, cache_location=pickle_cache):
        with open(cache_location, 'rb') as f: 
            return pickle.load(f)

    def cache(self):
        with open(self.cache_location, 'wb') as cache:
            pickle.dump(self, cache)    

    def init_html(self):
        print('Scraping table of contents data from website')
        self.toc.load_dom()
        self.chapters = self.toc.get_chapters()
        
        print('Scraping chapter data from website')
        for chapter in tqdm(self.chapters):
            chapter.save_html()

    def init_epub(self):
        self.book = epub.EpubBook()
        self.book.set_identifier(str(uuid.uuid4()))
        self.book.set_title(self.title)
        self.book.set_language('en')
        self.book.add_author(self.author)
        
        #css
        self.book.add_item(Book.get_css())

    def get_css(filename='kindle.css', uid='style_default'):
        with open(filename, 'r') as css:
            return epub.EpubItem(uid=uid, file_name="style/"+filename, media_type="text/css", content=css.read())

    def generate_epub(self):
        print('Initializing epub')
        self.init_epub()

        #spine is used when navigating forward and backward through the epub
        #first element is 'nav' followed by each epub.EpubHtml chapter in order
        self.book.spine = ['nav']

        sections = OrderedDict()
        current_section = None

        print('Generate chapters')
        for chapter in tqdm(self.chapters):
            chapter.load_dom()
            epub_chapter = chapter.to_epub(Book.get_css())

            self.book.add_item(epub_chapter)
            self.book.spine.append(epub_chapter)

            epub_section = chapter.get_epub_section()
            if 'interlude' not in epub_section.lower():
                current_section = epub_section
            else:
                epub_section = current_section

            if epub_section not in sections:
                sections[epub_section] = []
            sections[epub_section].append(epub_chapter)

        print('Generating table of contents')
        self.book.toc = [(epub.Section(section), tuple(chapters)) for section, chapters in tqdm(sections.items())]
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        print('Finished genetaring ebook')
        return self.book
        
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-c', '--clear-cache', dest='clear', default = False, action = 'store_true', help='Set to download a local copy of the website, clears local cache if it exists')
    parser.add_option('-a', '--author', dest='author', default='Wildbow', help='Author of ebook')
    parser.add_option('-t', '--title', dest='title', default='Parahumans - Worm', help='Title of ebook')
    parser.add_option('-u', '--url', dest='url', default='https://parahumans.wordpress.com/table-of-contents/', help='URL to the table of contents of the webpage to scrape')
    parser.add_option('-o', '--output', dest='output', default='parahumans.epub', help='Epub file to output')

    (options, args) = parser.parse_args()

    book = None

    if os.path.isfile(pickle_cache):
        book = Book.restore()

    if options.clear or book is None:
        book = Book(options.url, options.title, options.author)
        book.init_html()
        book.cache()

    try:
        # write to the file
        epub.write_epub(options.output, book.generate_epub(), {})
    except Exception as e:
        print(traceback.format_exc())
        book.cache()
