import lxml.html
from lxml.cssselect import CSSSelector
from collections import OrderedDict
from lxml.etree import tostring
from itertools import chain
from urllib.request import urlopen
from ebooklib import epub
import pickle, uuid, re

class Chapter:
    title_class = 'entry-title'
    chapter_class = 'entry-content'
    section_regex = '^(\w*) \d.*$'
    
    def __init__(self, url):
        self.url = url
        self.tree = None
        self.title = None
        self.text_markup = None

    def __getstate__(self):
        odict = self.__dict__.copy()
        if 'tree' in odict:
            del odict['tree']
        return odict
    
    def load_dom(self, refresh=False):
        if self.tree is None or refresh:
            response = urlopen(self.url)
            self.tree = lxml.html.fromstring(response.read().decode('utf-8', 'ignore'))
            response.close()
        return self.tree 

    def stringify_children(self, node):
        parts = ([node.text] +
                list(chain(*([c.text, tostring(c), c.tail] for c in node.getchildren()))) +
                [node.tail])
        # filter removes possible Nones in texts and tails
        return ''.join(filter(None, parts))     
        
    def get_title(self, refresh=False):
        if self.title is None or refresh:
            sel = CSSSelector('h1.entry-title a, h1.entry-title')
            for t in sel(self.load_dom(refresh)):
                self.title = t.text
    
        return self.title

    #need to figure out how to prun next/prev chapter nodes when scrping body
    def get_text(self, refresh=False):
        if self.text_markup is None or refresh:
            sel = CSSSelector('div.entry-content p')

            match = sel(self.load_dom(refresh))

            self.text_markup = ''.join(tostring(p, encoding='unicode', pretty_print=True) for p in match if len(p.getchildren()) == 0)

        return self.text_markup

    def get_epub_section(self, refresh=False):
        return re.match(Chapter.section_regex, self.get_title(refresh)).group(1)

    def get_epub_filename(self, refresh=False):
        return self.get_title(refresh).replace(' ', '_') + '.xhtml'

    def to_epub(self, css, refresh=False):
        epub_chapter = epub.EpubHtml(title=self.get_title(refresh), file_name=self.get_epub_filename(refresh), lang='hr')
        epub_chapter.content='<html><body><h1>'+self.get_title(refresh)+'</h1>'+self.get_text(refresh)+'</body></html>'
        epub_chapter.add_item(css)
        return epub_chapter
        
class TableOfContents:
    toc_entry_class = 'entry-content'
    
    def __init__(self, url, cache_location='./cache/parahumans'):
        self.url = url
        self.cache_location = cache_location
        self.tree = None
        self.chapters = OrderedDict()

    def __getstate__(self):
        odict = self.__dict__.copy()
        if 'tree' in odict:
            del odict['tree']
        return odict

    @classmethod
    def restore(cls, cache_location='./cache/parahumans'):
        with open(cache_location, 'rb') as f: 
            return pickle.load(f)
        
    def load_dom(self, refresh=False):
        if self.tree is None or refresh:
            print('loading webpage ' + self.url)
            response = urlopen(self.url)
            self.tree = lxml.html.fromstring(response.read().decode('utf-8', 'ignore'))
            response.close()
        return self.tree

    def cache(self):
        with open(self.cache_location, 'wb') as cache:
            pickle.dump(self, cache)

    def get_chapters(self, refresh=False):
        if len(self.chapters) == 0 or refresh:
            sel = CSSSelector('div.entry-content a:not([href*="share"])')
            for link in sel(self.load_dom()):
                href = link.get('href')
                if not href.startswith('https://'):
                    href = 'https://' + href

                if href not in self.chapters:
                    self.chapters[href] = Chapter(href)

        return self.chapters.values()        

    def to_epub(self, book, css, refresh=False):
        sections = OrderedDict()
        chapters = []

        for chapter in self.get_chapters(refresh):
            epub_chapter = chapter.to_epub(css)
            chapters.append(epub_chapter)
            epub_section = chapter.get_epub_section(refresh)

            if epub_section not in sections:
                sections[epub_section] = []
            sections[epub_section].append(epub_chapter)

        book.toc = [(epub.Section(section), tuple(chapters)) for section, chapters in sections.items()]

        return chapters

class Book:
    def __init__(self, toc_url, title, author):
        self.toc = TableOfContents(toc_url)
        self.title = title
        self.author = author
        self.init_epub()

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

    def generate_from_web(self, refresh=False):
        chapters = self.toc.to_epub(self.book, Book.get_css(), refresh)

        #spine is used when navigating forward and backward through the epub
        #first element is 'nav' followed by each epub.EpubHtml chapter in order
        self.book.spine = ['nav']

        for chapter in chapters:
            self.book.add_item(chapter)
            self.book.spine.append(chapter)

        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())

        return self.book
        
if __name__ == '__main__':
    book = Book('https://parahumans.wordpress.com/table-of-TableOfContents/', 'Parahumans - Worm', 'Wildbow')

    book.toc.chapters['https://parahumans.wordpress.com/2013/03/05/scourge-19-5/'] = Chapter('https://parahumans.wordpress.com/2013/03/05/scourge-19-5/')
    book.toc.chapters['https://parahumans.wordpress.com/category/stories-arcs-1-10/arc-3-agitation/3-05/'] = Chapter('https://parahumans.wordpress.com/category/stories-arcs-1-10/arc-3-agitation/3-05/')

    # write to the file
    epub.write_epub('test.epub', book.generate_from_web(), {})
