import lxml.html
from lxml.cssselect import CSSSelector
from urllib.request import urlopen
from urllib import parse
from ebooklib import epub
import uuid, re, os, hashlib

class Chapter:    
    def __init__(self, url, config):
        self.config = config
        self.cache_filename = hashlib.md5(url.encode('utf-8')).hexdigest()+'.html'
        self.url = Chapter.clean_url(url)
        self.tree = None
        self.title = None
        self.text_markup = None

    def clean_url(url):
        url = parse.urlsplit(url)
        url = list(url)
        url[2] = parse.quote(url[2])
        url = parse.urlunsplit(url)

        return url

    def load_html(self):
        if not os.path.isfile(os.path.join(self.config.cache, self.cache_filename)):
            response = urlopen(self.url)
            content = response.read().decode('utf-8', 'ignore')
            response.close()

            with open(os.path.join(self.config.cache, self.cache_filename), 'w') as out:
                out.write(content)

        with open(os.path.join(self.config.cache, self.cache_filename), 'r') as f:
            self.tree = lxml.html.fromstring(f.read())

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
        return re.match(self.config.book.chapter.section_regex, self.get_title()).group(1)

    def get_epub_filename(self):
        title = self.get_title()      
        remove = [' ', '#', '\t', ':', ' '] #the last one isnt a normal space...
        for c in remove:
            title = title.replace(c, '_')
        return title + '.xhtml'

    def to_epub(self, css, chapter_text_callback):
        epub_chapter = epub.EpubHtml(title=self.get_title(), file_name=self.get_epub_filename(), lang='hr')
        epub_chapter.content='<html><body><h1>'+self.get_title()+'</h1>'+self.get_text(chapter_text_callback)+'</body></html>'
        epub_chapter.add_item(css)
        return epub_chapter
