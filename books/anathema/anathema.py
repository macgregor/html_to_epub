from lib.callbacks import Callbacks
from lxml.etree import tostring
import re, logging

class AnathemaCallbacks(Callbacks):
    arc_number_only_regex = '^(\d+)\\.(\d+)$'
    section_first_regex = '^(\D+)\s*(\d+)\\.(\d+)\s*(.*)$'
    section_last_regex = '^(\d+)\\.(\d+)\s*(\D+)\s*(.*)$'

    def __init__(self, config):
        logging.getLogger().debug('Instantiating AnathemaCallbacks class')
        self.config = config
        self.sections = dict()

    def chapter_next_callback(self, selector_matches):
        for match in selector_matches:
            logging.getLogger().debug(match.get('href'))
            if 'next' in tostring(match, encoding='unicode').lower() and match.get('href') != 'https://anathemaserial.wordpress.com/bonus-incentive/':                
                    return match.get('href')

        return None

    # have to sort the entire list because that 1 chapter is out of order in the ToC page
    def sort_chapters(self, chapters):
        sorted_chapters = sorted(chapters, key=lambda c: (self.normalize_title(c.title)[0], self.normalize_title(c.title)[1]))
        return sorted_chapters

    def chapter_title_callback(self, selector_matches):
        (arc_num, arc_chapter, arc_name, extra) = self.normalize_title(selector_matches[0].text)

        return  str(arc_num) + '.' + str(arc_chapter) + ' ' + arc_name + extra

    def chapter_text_callback(self, selector_match):
        if len(selector_match.cssselect('a')) == 0:
            return selector_match
        else:
            return None

    def chapter_section_callback(self, selector_matches):
        title = selector_matches[0].text

        (arc_num, arc_chapter, arc_name, extra) = self.normalize_title(title)

        if arc_name is not None and arc_num not in self.sections:
            self.sections[arc_num] = arc_name

        return self.sections[arc_num]

    '''
    This guy was not very consistent with his chapter naming. Sometimes its just the arc and chapter number,
    other times he throws in the arc name either before or after the numbers. To make things even mor fun he
    threw in some out of order stories in the table of contents page (e.g. 7.9 Interlude). If I dont hard code
    that chapter or completely change how I parse the table of contents to account for this edge case, chapter 7
    will show up as "Interlude" and not "Beacon". This also forced me to add a new callback to order the chapters
    so chapter 7.9 would appear in the right place in the book.

    This fucntion normalizes the chapter naming, returning a tuple in the form (arc_num, arc_chapter, arc_name, extra)
    letting other callback functions uses the pieces it cares about predictably.

    Web scraping is hard.
    '''
    def normalize_title(self, title):
        # dude put this random one out of order on the page, not sure how to do this elegantly so hard coding it :\
        if title == '7.9 Interlude':
            return (7, 9, 'Beacon', ' Interlude')

        # this one is weird too, if i dont include it in the Mascot arc it throws off the toc numbering in the epub
        if title == 'Prologue':
            return (1, 0, 'Mascot', ' Prologue')

        match = re.match(AnathemaCallbacks.arc_number_only_regex, title)
        if match is not None:
            return (int(match.group(1)), int(match.group(2)), self.sections[int(match.group(1))], '')

        match = re.match(AnathemaCallbacks.section_first_regex, title)
        if match is not None:
            return (int(match.group(2)), int(match.group(3)), match.group(1), match.group(4))

        match = re.match(AnathemaCallbacks.section_last_regex, title)
        if match is not None:
            return (int(match.group(1)), int(match.group(2)), match.group(3), match.group(4))
