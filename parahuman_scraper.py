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
        
class Contents:
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

    def to_epub(self, book, css):
        sections = OrderedDict()
        chapters = []

        for chapter in self.get_chapters():
            epub_chapter = chapter.to_epub(css)
            chapters.append(epub_chapter)
            book.add_item(epub_chapter)

            print(chapter.get_epub_section())

            if chapter.get_epub_section() not in sections:
                sections[chapter.get_epub_section()] = []
            sections[chapter.get_epub_section()].append(epub_chapter)

        book.toc = [(epub.Section(section), tuple(chapters)) for section, chapters in sections.items()]
        
        # basic spine
        book.spine = ['nav'] + chapters
        return book
        
if __name__ == '__main__':
    book = epub.EpubBook()

    # set metadata
    book.set_identifier(str(uuid.uuid4()))
    book.set_title('Parahumans - Worm')
    book.set_language('en')

    book.add_author('Wildbow')

    toc = Contents('https://parahumans.wordpress.com/table-of-contents/')
    toc.chapters['https://parahumans.wordpress.com/2013/03/05/scourge-19-5/'] = Chapter('https://parahumans.wordpress.com/2013/03/05/scourge-19-5/')
    toc.chapters['https://parahumans.wordpress.com/category/stories-arcs-1-10/arc-3-agitation/3-05/'] = Chapter('https://parahumans.wordpress.com/category/stories-arcs-1-10/arc-3-agitation/3-05/')

    # define CSS style
    toc_css = open('toc.css', 'r')
    style = toc_css.read()
    toc_css.close()

    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)

    kindle_css = open('kindle.css', 'r')
    style = kindle_css.read()
    kindle_css.close()

    default_css = epub.EpubItem(uid="style_default", file_name="style/default.css", media_type="text/css", content=style)

    # add CSS file
    book.add_item(nav_css)
    book.add_item(default_css)    

    book = toc.to_epub(book, default_css)

    # add default NCX and Nav file
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # write to the file
    epub.write_epub('test.epub', book, {})
