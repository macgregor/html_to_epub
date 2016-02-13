from BeautifulSoup import BeautifulSoup
import urllib2

class Chapter:
    title_class = 'entry-title'
    chapter_class = 'entry-content'
    
    def __init__(self, url):
        self.url = url
        self.soup = None
        self.title = None
        self.text_markup = None
    
    def load(self, refresh=False):
        if self.soup is None or refresh:
            self.soup = BeautifulSoup(urllib2.urlopen(self.url))
        return self.soup
        
    def get_title(self, refresh=False):
        if self.title is None or refresh:
            self.title = self.load().find('h1', {'class': Chapter.title_class}).find('a').contents[0]
    
        return self.title
        
    def get_text_markup(self, refresh=False):
        if self.text_markup is None or refresh:
            self.text_markup = self.load().find('div', {'class': Chapter.chapter_class}).findAll('p')
        
        return self.text_markup
    
    def get_text(self, refresh=False):
        return ''.join(p.text for p in self.get_text_markup(refresh))
        
class Contents:
    toc_entry_class = 'entry-content'
    
    def __init__(self, url):
        self.url = url
        self.chapters = []
        
    def load(self, refresh=False):
        if self.soup is None or refresh:
            self.soup = BeautifulSoup(urllib2.urlopen(self.url))
        return self.soup
        
    def get_chapters(self, refresh=False):
        if len(self.chapters) == 0 or refresh:
            for link in self.load().find('div', {'class': toc_entry_point}).findAll('a'):
                chapters.append(Chapter(link['href']))
        return self.chapters
        
if __name__ == '__main__':
    toc = Contents('https://parahumans.wordpress.com/table-of-contents/')
    
    for chapter in toc.get_chapters():
        print chapter.get_title()