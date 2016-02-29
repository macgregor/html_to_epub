from lxml.cssselect import CSSSelector
from lxml.etree import tostring
from ebooklib import epub
import uuid, logging

from .util import Network

'''
Chapter class - parses a web page for the chapter's title, ToC section and chapter text.
                Also responsible for turning this into an epub.EpubHtml object
'''
class Chapter:    
    def __init__(self, url, config, callbacks):
        self.config = config
        self.callbacks = callbacks
        self.url = Network.clean_url(url)
        self.cache_filename = Network.cache_filename(self.config.cache, self.url)
        self.next = None
        self.tree = None
        self.title = None
        self.epub_section = None
        self.epub_filename = None
        self.text_markup = None

    def __str__(self):
        format_str = '\nChapter{{\n  url: {}\n  title: {}\n  epub_section: {}\n  epub_filename: {}\n}}'
        return format_str.format(self.url, str(self.title), str(self.epub_section), str(self.epub_filename))

    '''
    Cache (if necessary) and load html dom into memory
    '''
    def load_html(self):
        self.tree = Network.load_and_cache_html(self.url, self.cache_filename)

        # initalize chapter fields in case __str__ is called
        self.get_title()
        self.get_epub_section()
        self.get_epub_filename()

        logging.getLogger().debug(self)

        return self.tree
    
    '''
    Parse the chapter title from the dom
    '''
    def get_title(self):
        match = CSSSelector(self.config.book.chapter.title_css_selector)
        self.title = self.callbacks.chapter_title_callback(match(self.tree))
    
        return self.title

    '''
    Parse the chapter text from the dom
    '''
    def get_text(self):
        match = CSSSelector(self.config.book.chapter.text_css_selector)

        paragraphs = []
        for p in match(self.tree):
            # call user callback on each matched element
            p = self.callbacks.chapter_text_callback(p)

            # if the user callback returns None we ignore this element
            if p is not None:
                #to string will give us the strong representation of the dom, including html markup which the epub can render
                paragraphs.append(tostring(p, encoding='unicode'))

        
        return ''.join(paragraphs)

    '''
    Construct the next chapter object from the url parsed from the dom
    '''
    def get_next_chapter(self):
        match = CSSSelector(self.config.book.chapter.next_chapter_css_selector)

        url = self.callbacks.chapter_next_callback(match(self.tree))
        
        if url is not None:
            self.next = Chapter(url ,self.config, self.callbacks)

        return self.next

    '''
    Parse the ToC section from the dom, generally this comes from manipulating the chapter title

    TODO: this should be optional
    '''
    def get_epub_section(self):
        match = CSSSelector(self.config.book.chapter.section_css_selector)

        self.epub_section = self.callbacks.chapter_section_callback(match(self.tree))

        return self.epub_section

    '''
    Generate the epub's internal filename for the chapter. Epubs are basically archives filled with html files
    tied together by some navigational structures
    '''
    def get_epub_filename(self):
        title = self.get_title()
        
        # there are some illegal character for epub file names
        # I cant find a list so I update it when I encounter problems
        remove = [' ', '#', '\t', ':', ' '] #the last one isnt a normal space...
        for c in remove:
            title = title.replace(c, '_')

        self.epub_filename = title + '.xhtml'
        return self.epub_filename

    '''
    Generate an epub.EpubHtml object based on the data parsed from the dom. Pass in the css object
    so we can apply the styling without constructing a new one for each chapter object
    '''
    def to_epub(self, css):
        chapter_title = self.get_title()

        epub_chapter = epub.EpubHtml(title=chapter_title, file_name=self.get_epub_filename(), lang='hr')
        epub_chapter.content='<html><body><h1>'+chapter_title+'</h1>'+self.get_text()+'</body></html>'
        epub_chapter.add_item(css)

        return epub_chapter
