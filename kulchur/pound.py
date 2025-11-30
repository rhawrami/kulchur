from datetime import datetime
import re
import asyncio
import time
import warnings
from types import SimpleNamespace
from typing import (
    Optional, 
    Dict, 
    List, 
    Union, 
    Any,
)

import aiohttp
import requests
from bs4 import BeautifulSoup, Tag

from .recruits import (
    _parse_id, 
    _rm_double_space
)


class Pound:
    '''Pound: collect publicly available Goodreads author data.'''
    def __init__(self):
        '''GoodReads author data collector. Sequential and asynchronous capabilities available.'''
        self._soup: Optional[BeautifulSoup] = None
        self._info_main: Optional[Tag] = None
        self._author_url:  Optional[str] = None
    

    async def load_author_async(self,
                                session: aiohttp.ClientSession,
                                author_identifier: Optional[str] = None,
                                see_progress: bool = True) -> Optional['Pound']:
        '''
        load GoodReads author data asynchronously.
        
        :param session:
         an aiohttp.ClientSession object
        :param user_identifier:
         Unique Goodreads author ID, or URL to the author's page.
        :param see_progress:
         if True, prints progress statements and updates. If False, progress statements are suppressed. 
        '''
        if author_identifier:
            if re.match(r'^https://www.goodreads.com/author/show/\d*',author_identifier):
                author_identifier = author_identifier
            elif re.match(r'^\d+$', author_identifier):
                author_identifier = f'https://www.goodreads.com/author/show/{author_identifier}'
            else:
                raise ValueError('author_identifier must be full URL string OR identification serial number')
        else:
            raise ValueError('Provide author identification.')
        self.author_url = author_identifier

        a_id = _parse_id(self.author_url)
        
        try:
            print(f'{a_id} attempt @ {time.ctime()}') if see_progress else None
            
            async with session.get(url=self.author_url) as resp:
                if resp.status != 200:
                    raise Exception(f'Improper request respose: {resp.status} recieved for author {a_id}')
                
                text = await resp.text()
                soup = BeautifulSoup(text,'lxml')
                info_main = soup.find('div', class_='mainContentFloat')
                info_left = info_main.find('div', class_='leftContainer authorLeftContainer')
                info_right = info_main.find('div', class_='rightContainer')
                
                self._soup = soup
                self._info_main = info_main
                self._info_left = info_left
                self._info_right = info_right
                
                print(f'{a_id} pulled @ {time.ctime()}') if see_progress else None
                return self
            
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f'Timeout Error for author {a_id}')
        except aiohttp.ClientError:
            raise aiohttp.ClientError(f'Client Error for author {a_id}')
        except Exception as er:
            raise Exception(f'Unexpected Error for author {a_id}: {er}')
    

    def load_author(self,
                    author_identifier: Optional[str] = None,
                    see_progress: bool = None) -> Optional['Pound']:
        '''
        load GoodReads author data.

        :param author_identifier:
         Unique Goodreads author ID, or URL to the author's page.
        :param see_progress:
         if True, prints progress statements and updates. If False, progress statements are suppressed.
        '''
        if author_identifier:
            if re.match(r'^https://www.goodreads.com/author/show/\d*',author_identifier):
                author_identifier = author_identifier
            elif re.match(r'^\d+$', author_identifier):
                author_identifier = f'https://www.goodreads.com/author/show/{author_identifier}'
            else:
                raise ValueError('author_identifier must be full URL string OR identification serial number')
        else:
            raise ValueError('Provide author identification.')
        self.author_url = author_identifier

        a_id = _parse_id(self.author_url)
        
        try:
            print(f'{a_id} attempt @ {time.ctime()}') if see_progress else None

            resp = requests.get(self.author_url)
            if resp.status_code != 200:
                raise Exception(f'Improper request respose: {resp.status_code} recieved for author {a_id}')
            
            text = resp.text
            soup = BeautifulSoup(text,'lxml')
            info_main = soup.find('div', class_='mainContentFloat')
            info_left = info_main.find('div', class_='leftContainer authorLeftContainer')
            info_right = info_main.find('div', class_='rightContainer')
            
            self._soup = soup
            self._info_main = info_main
            self._info_left = info_left
            self._info_right = info_right
            
            print(f'{a_id} pulled @ {time.ctime()}') if see_progress else None
            return self
        
        except requests.HTTPError:
            raise requests.HTTPError(f'HTTP Error for author {a_id}')
        except Exception as er:
            raise Exception(f'Unexpected Error for author {a_id}: {er}')
        

    def _confirm_loaded(self) -> None:
        '''checks if attributes have been defined; raises error if not.'''
        if not self._soup:
            raise RuntimeError('Goodreads author not yet loaded; use "load_author" method prior to any "get_[author_attr]" methods')
    

    def get_name(self) -> Optional[str]:
        '''returns name of loaded Goodreads author.'''
        self._confirm_loaded()
        h1 = self._info_right.find('h1', class_='authorName')
        if h1:
            name = h1.find('span')
            return _rm_double_space(name.text.strip()) if name else None
        else:
            return None
    

    def get_id(self) -> Optional[str]:
        '''returns unique ID of loaded Goodreads author.'''
        self._confirm_loaded()
        return _parse_id(self.author_url)
    

    def get_image_url(self) -> Optional[str]:
        '''returns URL to loaded Goodreads author's image.'''
        self._confirm_loaded()
        try:
            img = self._info_left.find('img')
            img_url = img['src'].strip()
            return img_url if 'nophoto' not in img_url else None
        except Exception:
            return None
    

    def get_birth_place(self) -> Optional[str]:
        '''returns birth place of loaded Goodreads author.'''
        self._confirm_loaded()
        birth_place_header = self._info_right.find('div', class_ = 'dataTitle')
        if birth_place_header:
            if re.match(r'^Born$', birth_place_header.text.strip()):
                txt = self._info_right.text.strip()
                birth_place_messy = re.search(r'Born\n.*',txt)
                if birth_place_messy:
                    birth_place = re.sub(r'Born\nin|Born\n\s+in|Born\n', '', birth_place_messy.group(0).strip())
                    return _rm_double_space(birth_place.strip())
        return None


    def get_birth_date(self) -> Optional[str]:
        '''returns birth date (in "DD/MM/YY" format) of loaded Goodreads author.'''
        self._confirm_loaded()
        bd = self._info_right.find('div', {'itemprop': 'birthDate'})
        if bd:
            bdt = bd.text.strip()
            date_grps = re.match(r'^([A-z][a-z]+) (\d+), (\d+)$', bdt)
            if date_grps:
                # if year published is < 1000
                if len(date_grps.group(3)) < 4:
                    bdt = f'{date_grps.group(1)} {date_grps.group(2)}, {date_grps.group(3).zfill(4)}'
                birth_date = datetime.strptime(bdt,'%B %d, %Y').strftime('%m/%d/%Y')
                return birth_date
        else:
            return None
    

    def get_death_date(self) -> Optional[str]:
        '''returns death date (in "DD/MM/YY" format) of loaded Goodreads author.'''
        self._confirm_loaded()
        dd = self._info_right.find('div', {'itemprop': 'deathDate'})
        if dd:
            ddt = dd.text.strip()
            death_date = datetime.strptime(ddt,'%B %d, %Y').strftime('%m/%d/%Y')
            return death_date
        else:
            return None
        

    def get_top_genres(self) -> Optional[List[str]]:
        '''returns loaded Goodreads author's top genres.'''
        self._confirm_loaded()
        try:
            genre_title = [i for i in self._info_right.find_all('div', class_='dataTitle') if i.text == 'Genre'][0]
            genre_box = genre_title.find_next_siblings()[0]
            genres = []
            for genre in genre_box.find_all('a'):
                genres.append(genre.text.strip())
            return genres
        except Exception:
            return None
    

    def get_influences(self) -> Optional[List[Dict[str,str]]]:
        '''returns list of other authors that loaded Goodreads author is influenced by.'''
        self._confirm_loaded()
        try:
            data_titles = self._info_right.find_all('div', class_ = 'dataTitle')
            influence_txt = [dt for dt in data_titles if 'fluence' in dt.text][0]
            if 'fluence' in influence_txt.text:
                influence_box = influence_txt.find_next_sibling('div', class_ = 'dataItem').find_all('span')[-1]
                influences = []
                for author in influence_box.find_all('a'):
                    name = author.text.strip()
                    id_ = _parse_id(author['href'].strip())
                    influences.append(
                        {'author': name, 'id': id_}
                    )
                return influences if len(influences) > 0 else None
            else:
                return None
        except Exception:
            return None
    

    def get_description(self) -> Optional[str]:
        '''returns description of loaded Goodreads author.'''
        self._confirm_loaded()
        try:
            author_info = self._info_right.find('div', class_ = 'aboutAuthorInfo')
            info = author_info.find_all('span')[-1]
            return _rm_double_space(info.text.strip())
        except Exception:
            return None
    

    def get_follower_count(self) -> Optional[int]:
        '''returns number of users following loaded Goodreads author.'''
        self._confirm_loaded()
        try:
            h2 = self._info_left.find_all('h2')
            followers = [h.text.strip() for h in h2 if 'follower' in h.text.strip().lower()][0]
            follow_count_str = re.search(r'\(\d*.*\)',followers).group(0)
            follow_count = re.sub(r'\(|\)|,','',follow_count_str)
            return int(follow_count)
        except:
            return None
            

    def get_rating_count(self) -> Optional[int]:
        '''returns number of ratings given to loaded Goodreads author's works.'''
        self._confirm_loaded()
        try:
            agg_stats = self._info_right.find('div', class_ = 'hreview-aggregate')
            num_rate_str = agg_stats.find('span', {'itemprop': 'ratingCount'}).text.strip()
            num_rate = num_rate_str.replace(',','')
            return int(num_rate)
        except Exception:
            return None
    

    def get_review_count(self) -> Optional[int]:
        '''returns number of reviews given to loaded Goodreads author's works.'''
        self._confirm_loaded()
        try:
            agg_stats = self._info_right.find('div', class_ = 'hreview-aggregate')
            num_rev_str = agg_stats.find('span', {'itemprop': 'reviewCount'}).text.strip()
            num_rev = num_rev_str.replace(',','')
            return int(num_rev)
        except Exception:
            return None
    

    def get_rating(self) -> Optional[float]:
        '''returns loaded Goodread author's average book rating.'''
        self._confirm_loaded()
        try:
            agg_stats = self._info_right.find('div', class_ = 'hreview-aggregate')
            avg_rate = agg_stats.find('span', {'itemprop': 'ratingValue'}).text.strip()
            return float(avg_rate)
        except Exception:
            return None
    

    def get_books_sample(self) -> Optional[List[Dict[str,Any]]]:
        '''returns sample (max n = 10) of loaded Goodreads author's most popular books.'''
        # if anyone ever reads this: I know, this is very ugly. 
        # But it works most of the time probably. I haven't written any tests yet.
        self._confirm_loaded()
    
        agg_stats = self._info_right.find('div', class_ = 'hreview-aggregate')
        if agg_stats:
            books_tab = agg_stats.find_next_sibling('table').find_all('tr', {'itemtype': 'http://schema.org/Book'})
        else:
            return None
        
        books = []
        for bk in books_tab:
            elements = bk.find_all('td')
            if len(elements) > 1:
                bk_info = elements[1]   # second element contains all the info we need
            else:
                return None

            title_and_id = bk_info.find('a', class_ = 'bookTitle')
            try:
                bk_url = title_and_id['href'].strip()
                bk_id = _parse_id(bk_url)
                bk_title = _rm_double_space(title_and_id.find('span').text.strip())
            except Exception:
                continue    # we need title and ID, or else this entry is useless
            
            div_boxes = bk_info.find_all('div')
            if len(div_boxes):
                text_elements = div_boxes[-1].find('span', class_ = ['greyText', 'smallText', 'uitext'])
            
            if text_elements:
                try:
                    rate_stats = text_elements.find('span', class_ = 'minirating')
                    rating = re.search(r'\d.*avg rating|avg rating', rate_stats.text).group(0)
                    avg_rating_str = re.sub(r'avg rating|\s', '', rating)
                    avg_rating = float(avg_rating_str)
                except Exception:
                    avg_rating = None
                if avg_rating:
                    try:
                        num_rat = re.search(r'\d+ ratings|1 rating',rate_stats.text.replace(',','')).group(0)
                        num_rating_str = re.match(r'\d+',num_rat).group(0)
                        num_rating = int(num_rating_str)
                    except Exception:
                        num_rating = None
                else:
                    num_rating = None
                try:
                    pub_date = re.search(r'published\n+.*\d+',text_elements.text).group(0).strip()
                    publish_date_str = re.sub(r'published|\s', '', pub_date)
                    publish_date = int(publish_date_str)
                except Exception:
                    publish_date = None
            else:
                avg_rating = num_rating = publish_date = None
            
            bk_dat = {
                'title': bk_title,
                'id': bk_id,
                'first_published': publish_date,
                'rating': avg_rating,
                'rating_count': num_rating
            }
            books.append(bk_dat)
        return books if len(books) else None


    def get_quotes_sample(self) -> Optional[List[str]]:
        '''returns sample (max n = 3) list of top quotes by loaded Goodreads author.'''
        self._confirm_loaded()
        qt_title_bar = None
        for div in self._info_right.find_all('div', style = True):
            try:
                first_a = div.find('a')
                if re.search(r'^quotes by.*$',first_a.text.lower()):
                    qt_title_bar = div
            except AttributeError:
                continue
        if not qt_title_bar:
            return None
        qt_box = qt_title_bar.find_next_sibling('div')
        if qt_box:
            quotes = []
            for qt in qt_box.find_all('div', class_ = ['quote', 'mediumText']):
                try:
                    qt_txt_all = qt.find('div', class_ = 'quoteText').text
                    qt_txt = re.search(r'“.*”',qt_txt_all).group(0)
                    qt_txt = re.sub(r'“|”','',qt_txt)
                    qt_txt = _rm_double_space(qt_txt)
                    quotes.append(qt_txt)
                except AttributeError:
                    continue
            return None if not len(quotes) else quotes
        return None
        

    def get_all_data(self,
                     exclude_attrs: Optional[List[str]] = None,
                     to_dict: bool = True) -> Union[Dict[str,Any],SimpleNamespace]:
        '''
        returns collection of data from loaded Goodreads author.

        :param exclude_attrs:
         list of user attributes to exclude. If None, collects all available attributes. See below for available author attributes.
        :param to_dict:
         if True, converts data collection to Dict format; otherwise, data is returned in SimpleNamespace format.
        
        ------------------------------------------------------------------------------
        returns the following available attributes:
        - **url** (str): URL to Goodreads author page
        - **id** (str): unique Goodreads author ID
        - **name** (str): author's name
        - **description** (str): description of author
        - **image_url** (str): URL to author's cover picture
        - **birth_place** (str): author's place of birth
        - **birth** (str): author's birth date (in "MM/DD/YYYY" format)
        - **death** (str): author's death date (in "MM/DD/YYYY" format)
        - **top_genres** (List[str]): list of author's favorite genres
            - e.g., ['Fiction', 'Historical Fiction', 'Alternate History']
        - **influences** (List[Dict]): list of author's influences
        - **books_sample** (List[Dict]): sample (max n = 10) of loaded Goodreads author's most popular books
        - **quotes)sample** (List[str]): sample (max n = 3) of quotes by loaded Goodreads author
        - **rating** (str): average of user ratings given to author's works (1-5)
        - **rating_count** (int): number of user ratings given to author's works
        - **review_count** (int): number of user reviews given to author's works
        - **follower_count** (int): number of users are following the author
        '''
        self._confirm_loaded()
        attr_fn_map = {
            'url': lambda: self.author_url,
            'id': self.get_id,
            'name': self.get_name,
            'description': self.get_description,
            'image_url': self.get_image_url,
            'birth_place': self.get_birth_place,
            'birth': self.get_birth_date,
            'death': self.get_death_date,
            'top_genres': self.get_top_genres,
            'influences': self.get_influences,
            'books_sample': self.get_books_sample,
            'quotes_sample': self.get_quotes_sample,
            'rating': self.get_rating,
            'rating_count': self.get_rating_count,
            'review_count': self.get_review_count,
            'follower_count': self.get_follower_count
        }
        exclude_set = set(exclude_attrs) if exclude_attrs else set([])
        authr_dict = {}
        for attr,fn in attr_fn_map.items():
            if exclude_attrs:
                if attr not in exclude_set:
                    authr_dict[attr] = fn()
            else:
                authr_dict[attr] = fn()
        if len(authr_dict) == 0:
            warnings.warn('Warning: returning empty object; param exclude_attrs should not include all attrs') 
            return authr_dict if to_dict else SimpleNamespace()
        return authr_dict if to_dict else SimpleNamespace(**authr_dict)
