import lxml.html
from lxml.cssselect import CSSSelector
from lxml.etree import tostring
from urllib.request import urlopen
from urllib import parse
from ebooklib import epub
import uuid, re, os, yaml

class Chapter:
    section_regex = '^(\w+)\s*.*$'
    
    def __init__(self, url, cache_location):
        self.cache_location = cache_location
        self.cache_filename = str(uuid.uuid4())+'.html'
        self.url = Chapter.clean_url(url)
        self.tree = None
        self.title = None
        self.text_markup = None

    def __getstate__(self):
        odict = self.__dict__.copy()
        odict['tree'] = None
        return odict

    def clean_url(url):
        url = parse.urlsplit(url)
        url = list(url)
        url[2] = parse.quote(url[2])
        url = parse.urlunsplit(url)

        return url

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
                    paragraphs.append(tostring(p, encoding='unicode'))


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
