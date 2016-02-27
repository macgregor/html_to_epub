from lxml.cssselect import CSSSelector
from ebooklib import epub
import uuid, re, logging

from .util import Network

class Chapter:    
    def __init__(self, url, config):
        self.config = config
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
        sel = CSSSelector(self.config.book.chapter.title_css_selector)
        for t in sel(self.tree):
            self.title = t.text
    
        return self.title

    def get_text(self, callback=None):
        sel = CSSSelector(self.config.book.chapter.text_css_selector)
        match = sel(self.tree)

        if callback is not None:
            match = callback(match)

        self.text_markup = ''.join(match)

        return self.text_markup

    def get_epub_section(self):
        self.epub_section = re.match(self.config.book.chapter.section_regex, self.get_title()).group(1)

        return self.epub_section

    def get_epub_filename(self):
        title = self.get_title()      
        remove = [' ', '#', '\t', ':', ' '] #the last one isnt a normal space...
        for c in remove:
            title = title.replace(c, '_')

        self.epub_filename = title + '.xhtml'
        return self.epub_filename

    def to_epub(self, css, chapter_text_callback):
        chapter_title = self.get_title()

        epub_chapter = epub.EpubHtml(title=chapter_title, file_name=self.get_epub_filename(), lang='hr')
        epub_chapter.content='<html><body><h1>'+chapter_title+'</h1>'+self.get_text(chapter_text_callback)+'</body></html>'
        epub_chapter.add_item(css)

        return epub_chapter
