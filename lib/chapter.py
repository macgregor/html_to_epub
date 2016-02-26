import lxml.html
from lxml.cssselect import CSSSelector
from urllib.request import urlopen
from urllib import parse
from ebooklib import epub
import uuid, re, os, hashlib

class Chapter:    
    def __init__(self, url, config, debug=False):
        self.config = config
        self.debug = debug
        self.cache_filename = os.path.join(self.config.cache, hashlib.md5(url.encode('utf-8')).hexdigest()+'.html')
        self.url = Chapter.clean_url(url)
        self.tree = None
        self.title = None
        self.epub_section = None
        self.epub_filename = None
        self.text_markup = None

    def clean_url(url):
        url = parse.urlsplit(url)
        url = list(url)
        url[2] = parse.quote(url[2])
        url = parse.urlunsplit(url)

        return url

    def __str__(self):
        format_str = 'Chapter[\n\turl: {}\n\ttitle: {}\n\tepub_section: {}\n\tepub_filename: {}\n]'
        return format_str.format(self.url, self.title, self.epub_section, self.epub_filename)

    def load_html(self):
        
        if not os.path.isfile(self.cache_filename):
            if self.debug:
                print('Cache miss - Downloading ' + self.url + ' to ' + self.cache_filename)

            response = urlopen(self.url)
            content = response.read().decode('utf-8', 'ignore')
            response.close()

            with open(os.path.join(self.config.cache, self.cache_filename), 'w') as f:
                f.write(content)

        if self.debug:
            print('Loading html dom from ' + self.cache_filename)

        with open(self.cache_filename, 'r') as f:
            self.tree = lxml.html.fromstring(f.read())

        self.get_title()
        self.get_epub_section()
        self.get_epub_filename()

        if self.debug:
            print(self)

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
