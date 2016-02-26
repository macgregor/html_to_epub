import yaml

class TableOfContentsConfig:
    def __init__(self, yml):
        self.url = yml['url']
        self.chapter_link_css_selector = yml['chapter_link_css_selector']

class ChapterConfig:
    def __init__(self, yml):
        self.title_css_selector = yml['title_css_selector']
        self.text_css_selector = yml['text_css_selector']
        self.section_regex = yml['section_regex']

class BookConfig:
    def __init__(self, yml):
        self.title = yml['title']
        self.author = yml['author']
        self.epub_filename = yml['epub_filename']
        self.table_of_contents = TableOfContentsConfig(yml['table_of_contents'])
        self.chapter = ChapterConfig(yml['chapter'])
        self.css_filename = yml['css_filename']

class Config:

    def __init__(self, filename):
        with open(filename, 'r') as ymlfile:
            config = yaml.load(ymlfile)

        self.book = BookConfig(config['book'])
        self.cache = config['cache']
