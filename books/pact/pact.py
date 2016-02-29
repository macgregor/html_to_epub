from lib.callbacks import Callbacks
from lxml.etree import tostring
import re, logging

class PactCallbacks(Callbacks):

    def __init__(self, config):
        self.config = config
        self.sections = dict()

    def chapter_next_callback(self, selector_matches):
        for match in selector_matches:
            if 'Next Chapter' == match.get('title') or 'Next Chapter' in tostring(match, encoding='unicode'):
                return match.get('href')

        return None

    def chapter_text_callback(self, selector_match):
        if len(selector_match.cssselect('a')) == 0:
            return selector_match
        else:
            return None

    def chapter_title_callback(self, selector_matches):
        title = None
        for match in selector_matches:
            if match.text is not None:
                title = match.text
                break
        return title

    def chapter_section_callback(self, selector_matches):
        section_regex = '^(\D*)(\d*)\\.*(\d*).*$'
        
        title = self.chapter_title_callback(selector_matches)
        matches = re.match(section_regex, title)

        if 'Gathered Pages' in matches.group(1) or 'Histories' in matches.group(1):
            return self.sections[matches.group(2)]
        else:
            self.sections[matches.group(2)] = matches.group(1)
            return matches.group(1)
