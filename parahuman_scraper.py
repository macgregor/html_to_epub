import lxml.html
from lxml.cssselect import CSSSelector
from collections import OrderedDict
from lxml.etree import tostring
from itertools import chain
import urllib2, pickle

class Chapter:
    title_class = 'entry-title'
    chapter_class = 'entry-content'
    
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
            response = urllib2.urlopen(self.url.encode('utf-8'))
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
            for t in sel(self.load_dom()):
                self.title = t.text
    
        return self.title
    
    #need to figure out how to prun next/prev chapter nodes when scrping body
    def get_text(self, refresh=False):
        if self.text_markup is None or refresh:
            sel = CSSSelector('div.entry-content p')

            match = sel(self.load_dom())

            self.text_markup = ''.join(self.stringify_children(p) for p in match)

        return self.text_markup
        
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
            print 'loading webpage ' + self.url
            response = urllib2.urlopen(self.url.encode('utf-8'))
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
            #for link in self.load_dom().find('div', {'class': Contents.toc_entry_class}).findAll('a'):
                href = link.get('href')
                if not href.startswith('https://'):
                    href = 'https://' + href

                if href not in self.chapters:
                #if href not in self.chapters and 'facebook' not in href and 'twitter' not in href:
                    self.chapters[href] = Chapter(href)

        return self.chapters.values()
        
if __name__ == '__main__':
    toc = Contents('https://parahumans.wordpress.com/table-of-contents/')
    toc.chapters['https://parahumans.wordpress.com/2013/03/05/scourge-19-5/'] = Chapter('https://parahumans.wordpress.com/2013/03/05/scourge-19-5/')
    #toc.chapters['https://parahumans.wordpress.com/category/stories-arcs-1-10/arc-5-hive/5-06/'] = Chapter('https://parahumans.wordpress.com/category/stories-arcs-1-10/arc-5-hive/5-06/')

    #toc = Contents.restore()

    for chapter in toc.get_chapters():
        print chapter.url
        print chapter.get_title()
        print chapter.get_text()

    toc.cache()
