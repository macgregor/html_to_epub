from lxml.cssselect import CSSSelector
from lxml.etree import tostring
from ebooklib import epub
import uuid, logging

from .util import Network

class Chapter:    
    def __init__(self, url, config, htmlCallbacks):
        self.config = config
        self.htmlCallbacks = htmlCallbacks
        self.url = Network.clean_url(url)
        self.cache_filename = Network.cache_filename(self.config.cache, self.url)
        self.tree = None
        self.title = None
        self.epub_section = None
        self.epub_filename = None
        self.text_markup = None

    def __str__(self):
        format_str = '\nChapter{{\n  url: {}\n  title: {}\n  epub_section: {}\n  epub_filename: {}\n}}'
        return format_str.format(self.url, self.title, self.epub_section, self.epub_filename)

    def load_html(self):
        self.tree = Network.load_and_cache_html(self.url, self.cache_filename)

        self.get_title()
        self.get_epub_section()
        self.get_epub_filename()

        logging.getLogger().debug(self)

        return self.tree
        
    def get_title(self):
        match = CSSSelector(self.config.book.chapter.title_css_selector)
        self.title = self.htmlCallbacks.chapter_title_callback(match(self.tree))
    
        return self.title

    def get_text(self):
        match = CSSSelector(self.config.book.chapter.text_css_selector)

        paragraphs = []
        for p in match(self.tree):
            p = self.htmlCallbacks.chapter_text_callback(p)
            if p is not None:
                paragraphs.append(tostring(p, encoding='unicode'))

        return ''.join(paragraphs)

    def get_epub_section(self):
        match = CSSSelector(self.config.book.chapter.section_css_selector)

        self.epub_section = self.htmlCallbacks.chapter_section_callback(match(self.tree))

        return self.epub_section

    def get_epub_filename(self):
        title = self.get_title()      
        remove = [' ', '#', '\t', ':', ' '] #the last one isnt a normal space...
        for c in remove:
            title = title.replace(c, '_')

        self.epub_filename = title + '.xhtml'
        return self.epub_filename

    def to_epub(self, css):
        chapter_title = self.get_title()

        epub_chapter = epub.EpubHtml(title=chapter_title, file_name=self.get_epub_filename(), lang='hr')
        epub_chapter.content='<html><body><h1>'+chapter_title+'</h1>'+self.get_text()+'</body></html>'
        epub_chapter.add_item(css)

        return epub_chapter
