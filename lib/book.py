from collections import OrderedDict
from ebooklib import epub
from tqdm import tqdm
import pickle, uuid, yaml

from .chapter import Chapter
from .table_of_contents import TableOfContents

class Book:
    def __init__(self, toc_url, title, author, pickle_cache_location, html_cache_location):
        self.pickle_cache_location = pickle_cache_location
        self.html_cache_location = html_cache_location
        self.toc = TableOfContents(toc_url)
        self.chapters = None
        self.title = title
        self.author = author

    @classmethod
    def restore(cls, pickle_cache_location):
        with open(pickle_cache_location, 'rb') as f: 
            return pickle.load(f)

    def cache(self):
        with open(self.cache_location, 'wb') as cache:
            pickle.dump(self, cache)    

    def init_html(self):
        print('Scraping table of contents data from website')
        self.toc.load_dom()
        self.chapters = self.toc.get_chapters(self.html_cache_location)
        
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
