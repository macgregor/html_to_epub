import lxml.html
from urllib import parse
from urllib.request import urlopen
import os, logging, hashlib

class Network:
    def __init__():
        pass    

    @staticmethod
    def clean_url(url):
        url = parse.urlsplit(url)
        url = list(url)
        url[2] = parse.quote(url[2])
        url = parse.urlunsplit(url)

        return url

    @staticmethod
    def cache_filename(cache_dir, url):
        return os.path.join(cache_dir, hashlib.md5(url.encode('utf-8')).hexdigest()+'.html')

    @staticmethod
    def load_and_cache_html(url, cache_filename):
        
        if not os.path.isfile(cache_filename):
            logging.getLogger().debug('Cache miss - Downloading ' + url + ' to ' + cache_filename)

            response = urlopen(url)
            content = response.read().decode('utf-8', 'ignore')
            response.close()

            with open(cache_filename, 'w') as f:
                f.write(content)

        logging.getLogger().debug('Loading html dom from ' + cache_filename)

        with open(cache_filename, 'r') as f:
            return lxml.html.fromstring(f.read())
