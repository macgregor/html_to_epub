from BeautifulSoup import BeautifulSoup
from collections import OrderedDict
import urllib2, os, pickle

class Chapter:
    title_class = 'entry-title'
    chapter_class = 'entry-content'
    
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.title = None
        self.text_markup = None

    def __getstate__(self):
        odict = self.__dict__.copy()
        if 'soup' in odict:
            del odict['soup']
        return odict
    
    def load_dom(self, refresh=False):
        if self.soup is None or refresh:
            print 'missed the boat'
            response = urllib2.urlopen(self.url.encode('utf-8'))
            self.soup = BeautifulSoup(response.read().decode('utf-8', 'ignore'))
            response.close()
        return self.soup

    def decompose(self):
        if self.soup is not None:
            self.soup.decompose()
            self.soup = Nonet_markup = f.read()
        return self        
        
    def get_title(self, refresh=False):
        if self.title is None or refresh:
            header_title = self.load_dom().find('h1', {'class': Chapter.title_class})
            if header_title is not None:
                if header_title.find('a') is not None and header_title.find('a') is not None:
                    self.title = str(header_title.find('a').contents[0])
                elif header_title.contents[0] is not None:
                    self.title = str(header_title.contents[0])
    
        return self.title
    
    def get_text(self, refresh=False):
        if self.text_markup is None or refresh:
            dom = self.load_dom().find('div', {'class': Chapter.chapter_class}).findAll('p')
            del dom[0]
            del dom[len(dom)-1]
            self.text_markup = ''.join(p.text for p in dom)

        return self.text_markup
        
class Contents:
    toc_entry_class = 'entry-content'
    
    def __init__(self, url, cache_location='./cache/parahumans'):
        self.url = url
        self.cache_location = cache_location
        self.soup = None
        self.chapters = OrderedDict()

    def __getstate__(self):
        odict = self.__dict__.copy()
        if 'soup' in odict:
            del odict['soup']
        return odict

    @classmethod
    def restore(cls, cache_location='./cache/parahumans'):
        with open(cache_location, 'rb') as f: 
            return pickle.load(f)
        
    def load_dom(self, refresh=False):
        if self.soup is None or refresh:
            response = urllib2.urlopen(self.url.encode('utf-8'))
            self.soup = BeautifulSoup(response.read().decode('utf-8', 'ignore'))
            response.close()
        return self.soup

    def decompose(self):
        if self.soup is not None:
            self.soup.decompose()
            self.soup = None

    def cache(self):
        with open(self.cache_location, 'wb') as cache:
            pickle.dump(self, cache)

    def get_chapters(self, refresh=False):
        if len(self.chapters) == 0 or refresh:
            for link in self.load_dom().find('div', {'class': Contents.toc_entry_class}).findAll('a'):
                href = link['href']
                if not href.startswith('https://'):
                    href = 'https://' + href

                if href not in self.chapters and 'facebook' not in href and 'twitter' not in href:
                    self.chapters[href] = Chapter(href)

        return self.chapters.values()
        
if __name__ == '__main__':
    #toc = Contents('https://parahumans.wordpress.com/table-of-contents/')
    #toc.chapters['https://parahumans.wordpress.com/2012/06/30/plague-12-2/'] = Chapter('https://parahumans.wordpress.com/2012/06/30/plague-12-2/')
    #toc.chapters['https://parahumans.wordpress.com/2012/07/26/interlude-12%C2%BD/'] = Chapter('https://parahumans.wordpress.com/2012/07/26/interlude-12%C2%BD/')

    toc = Contents.restore()

    for chapter in toc.get_chapters():
        print chapter.get_title()
        #print chapter.get_text()

    toc.cache()
