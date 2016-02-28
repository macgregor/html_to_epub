from lib.callbacks import Callbacks
import re, logging

class PactCallbacks(Callbacks):

    def __init__(self, config):
        self.config = config
        self.sections = dict()

    def toc_chapters_callback(self, selector_match):
        href = selector_match.get('href')

        # fix a 404 on the table of contents page
        if href == 'https://pactwebserial.wordpress.com/2014/07/08/693/':
            selector_match.set('href', 'https://pactwebserial.wordpress.com/2014/07/08/signature-8-1/')
        elif href == '4031384495743822299':
            selector_match.set('href', 'https://pactwebserial.wordpress.com/2015/01/08/possession-15-2/')
        # chapter 6.11 is missing completely, this bad link in its place
        elif href == 'https://pactwebserial.wordpress.com/table-of-contents/':
            del selector_match.attrib['href']

        return super().toc_chapters_callback(selector_match)

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
