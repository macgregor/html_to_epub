from collections import OrderedDict
from ebooklib import epub
from tqdm import tqdm
import pickle, uuid, logging

from .chapter import Chapter

'''
Book class - handles most of the epub stuff as well as initalizing TableOfContents and Chapters 
'''
class Book:
    def __init__(self, config, callbacks):
        self.config = config
        self.callbacks = callbacks
        self.chapters = []
        self.title = config.book.title
        self.author = config.book.author

        with open(config.book.css_filename, 'r') as css:
            self.css = epub.EpubItem(uid='default', file_name="style/"+config.book.css_filename, media_type="text/css", content=css.read())

    '''
    Walks through a web page starting with config.book.entry_point, finding a 'next chapter' link and continueing until
    a next chapter link cannot be found. If a web page exists in the cache it will be loaded from the local file, 
    otherwise it will download the web page and then load the dom.

    Must be called before generate_epub. Thought of having generate_epub call this but since it does so much (downloading potentially
    hundreds of megs of data) I wanted to give the caller more control over it.
    '''
    def load_html(self):
        current = Chapter(self.config.book.entry_point, self.config, self.callbacks)
        current.load_html()
        self.chapters.append(current)

        next = current.get_next_chapter()
        max_iterations = self.config.max_chapter_iterations
        i = 0

        logging.getLogger().info('Walking through chapters (this could take a while)')
        with tqdm() as pbar:
            while next is not None and i < max_iterations:
                current = next
                current.load_html()

                self.chapters.append(current)

                next = current.get_next_chapter()
                i += 1
                pbar.update(1)

            if i == max_iterations:
                logging.getLogger().warn('Possible infinite loop detected, check your next_chapter_css_selector and/or chapter_next_callback callback function or increase config.max_chapter_iterations value')

            self.chapters = self.callbacks.sort_chapters(self.chapters)


    # initalizes some basic stuff needed by ebooklib: title, author, css, etc.
    def init_epub(self):
        self.book = epub.EpubBook()
        self.book.set_identifier(str(uuid.uuid4()))
        self.book.set_title(self.title)
        self.book.set_language('en')
        self.book.add_author(self.author)
        self.book.add_item(self.css)

    '''
    Turn our TableOfContetns and Chapter objects into epub format. At this point you should have called 
    init_html() or you will get NoneType exceptions because the dom isnt loaded.
    '''
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
            self.book.spine.append(epub_chapter) # the spin is yet another epub navigational thing. theres lots of that. 

            # TODO: make table of contents section optional
            epub_section = chapter.get_epub_section()

            if epub_section not in sections:
                sections[epub_section] = []
            sections[epub_section].append(epub_chapter)

        logging.getLogger().info('Generating table of contents')

        # TODO: make table of contents section optional
        self.book.toc = [(epub.Section(section), tuple(chapters)) for section, chapters in tqdm(sections.items(), disable=self.config.debug)]

        # this is some boiler plate to build the navigational structures required by epub
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        logging.getLogger().info('Finished genetaring ebook')
        return self.book
