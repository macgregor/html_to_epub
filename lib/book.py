from collections import OrderedDict
from ebooklib import epub
from tqdm import tqdm
import pickle, uuid, yaml, logging

from .chapter import Chapter
from .table_of_contents import TableOfContents

global debug

class Book:
    def __init__(self, config, callbacks):
        self.config = config
        self.callbacks = callbacks
        self.toc = TableOfContents(config, callbacks)
        self.chapters = []
        self.title = config.book.title
        self.author = config.book.author

        with open(config.book.css_filename, 'r') as css:
            self.css = epub.EpubItem(uid='default', file_name="style/"+config.book.css_filename, media_type="text/css", content=css.read())

    def load_html(self):
        logging.getLogger().info('Loading table of contents html')
        self.toc.load_html()
        self.chapters = self.toc.get_chapters()
        
        logging.getLogger().info('Loading chapter html (this could take a while)')
        for chapter in tqdm(self.chapters, disable=self.config.debug):
            chapter.load_html()

        self.chapters = self.callbacks.sort_chapters(self.chapters)

    def init_epub(self):
        self.book = epub.EpubBook()
        self.book.set_identifier(str(uuid.uuid4()))
        self.book.set_title(self.title)
        self.book.set_language('en')
        self.book.add_author(self.author)
        
        #css
        self.book.add_item(self.css)

    def generate_epub(self):
        logging.getLogger().info('Initializing epub')
        self.init_epub()

        #spine is used when navigating forward and backward through the epub
        #first element is 'nav' followed by each epub.EpubHtml chapter in order
        self.book.spine = ['nav']

        sections = OrderedDict()
        current_section = None

        logging.getLogger().info('Generate chapters')
        for chapter in tqdm(self.chapters, disable=self.config.debug):
            epub_chapter = chapter.to_epub(self.css)

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

        logging.getLogger().info('Generating table of contents')
        self.book.toc = [(epub.Section(section), tuple(chapters)) for section, chapters in tqdm(sections.items(), disable=self.config.debug)]
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        logging.getLogger().info('Finished genetaring ebook')
        return self.book
