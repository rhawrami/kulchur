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

import requests
import aiohttp
from bs4 import BeautifulSoup, Tag

from .recruits import (
    _check_soup, 
    _get_similar_books, 
    _parse_id, 
    _get_similar_books_async, 
    _get_script_el, 
    _rm_double_space
)


class Alexandria:
    '''Alexandria: collect publicly available Goodreads book data.'''
    def __init__(self):
        '''GoodReads book data collector. Async capabilities available.'''
        self._soup: Optional[BeautifulSoup] = None
        self._info_main: Optional[Tag] = None
        self._info_main_metadat: Optional[Tag] = None
        self._details: Optional[Tag] = None
        self.book_url:  Optional[str] = None
        

    async def load_book_async(self,
                              session: aiohttp.ClientSession,
                              book_identifier: str,
                              see_progress: bool = True) -> Optional['Alexandria']:
        '''
        load GoodReads book data asynchronously.

        :param session:
         an aiohttp.ClientSession object
        :param book_identifier:
         Unique Goodreads book ID, or URL to the book's page
        :param see_progress:
         if True, prints progress statements and updates. If False, progress statements are suppressed.

        ------------------------------------------------------------------------------------------------------------
        Alexandria takes in a book_identifier argument, with:
        - a full url string to the book; e.g., book_identifier = "https://www.goodreads.com/book/show/7144.Crime_and_Punishment"
        - a unique GoodReads book identifier string; e.g., book_identifier = "7144"
        '''
        if book_identifier:
            if re.match(r'^https://www.goodreads.com/book/show/\d*',book_identifier):
                book_identifier = book_identifier
            elif re.match(r'^\d+$', book_identifier):
                book_identifier = f'https://www.goodreads.com/book/show/{book_identifier}'
            else:
                raise ValueError('book_identifier must be full URL string OR identification serial number')
        else:
            raise ValueError('Alexandria requires book identifier.')
        self.book_url = book_identifier
        
        b_id = _parse_id(self.book_url)

        try:
            print(f'{b_id} attempt @ {time.ctime()}') if see_progress else None

            async with session.get(url=self.book_url) as resp:
                if resp.status != 200:
                    raise Exception(f'Improper request respose: {resp.status} recieved for book {b_id}')
                
                text = await resp.text()
                soup = BeautifulSoup(text,'lxml')
                
                info_main = soup.find('div', class_='BookPage__mainContent')
                info_main_metadat = info_main.find('div', class_='BookPageMetadataSection')
                details = info_main_metadat.find('div', class_='FeaturedDetails')

                self._soup = soup
                self._info_main = info_main
                self._info_main_metadat = info_main_metadat
                self._details = details
                
                print(f'{b_id} pulled @ {time.ctime()}') if see_progress else None
                return self
            
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(f'Timeout Error for {b_id}')
        except aiohttp.ClientError:
            raise aiohttp.ClientError(f'Client Error for {b_id}')
        except Exception as er:
            raise Exception(f'Unexpected Error for {b_id}: {er}')


    def load_book(self,
                  book_identifier: str,
                  see_progress: bool = True) -> Optional['Alexandria']:
        '''
        load GoodReads book data.

        :param book_identifier:
         Unique Goodreads book ID, or URL to the book's page.
        :param see_progress:
         if True, prints progress statements and updates. If False, progress statements are suppressed.

        ------------------------------------------------------------------------------------------------------------
        Alexandria takes in a book_identifier argument, with:
        - a full url string to the book; e.g., book_identifier = "https://www.goodreads.com/book/show/7144.Crime_and_Punishment"
        - a unique GoodReads book identifier string; e.g., book_identifier = "7144"
        '''
        if book_identifier:
            if re.match(r'^https://www.goodreads.com/book/show/\d*',book_identifier):
                book_identifier = book_identifier
            elif re.match(r'^\d+$', book_identifier):
                book_identifier = f'https://www.goodreads.com/book/show/{book_identifier}'
            else:
                raise ValueError('book_identifier must be full URL string OR identification serial number')
        else:
            raise ValueError('Alexandria requires book identifier.')
        self.book_url = book_identifier
            
        b_id = _parse_id(self.book_url)
        
        try:
            print(f'{b_id} attempt @ {time.ctime()}') if see_progress else None

            resp = requests.get(book_identifier)
            if resp.status_code != 200:
                raise Exception(f'Improper request respose: {resp.status_code} recieved for book {b_id}')
            
            text = resp.text
            soup = BeautifulSoup(text,'lxml')
            info_main = soup.find('div', class_='BookPage__mainContent')
            info_main_metadat = info_main.find('div', class_='BookPageMetadataSection')
            details = info_main_metadat.find('div', class_='FeaturedDetails')

            self._soup = soup
            self._info_main = info_main
            self._info_main_metadat = info_main_metadat
            self._details = details

            print(f'{b_id} pulled @ {time.ctime()}') if see_progress else None
            return self
        
        except requests.HTTPError:
            raise requests.HTTPError(f'HTTP Error for book {b_id}')
        except Exception as er:
            raise Exception(f'Unexpected Error for book {b_id}: {er}')
    

    def _confirm_loaded(self) -> None:
        '''checks if attributes have been defined; raises error if not.'''
        if not self._soup:
            raise RuntimeError('Goodreads book not yet loaded; use "load_book" method prior to any "get_[book_attr]" methods.')
    

    def get_title(self) -> Optional[str]:
        '''returns title of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main:
            return None
        t1 = self._info_main.find('div', class_='BookPageTitleSection__title').find('h1')
        return _check_soup(t1)
    

    def get_id(self) -> Optional[str]:
        '''returns unique ID of loaded Goodreads book.'''
        self._confirm_loaded()
        return _parse_id(self.book_url)
    

    def get_author_name(self) -> Optional[str]:
        '''returns author name of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        a_n = self._info_main_metadat.find('span', class_='ContributorLink__name')
        return _rm_double_space(_check_soup(a_n))
    

    def get_author_id(self) -> Optional[str]:
        '''returns unique author ID of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        a_url = self._info_main_metadat.find('a', class_='ContributorLink')
        if a_url:
            a_id = _parse_id(a_url['href'])
            return a_id
        else:
            return None
    

    def get_isbn(self) -> Optional[str]:
        '''returns ISBN of loaded Goodreads book.'''
        self._confirm_loaded()
        headscript = self._soup.find('head').find('script',{'type': 'application/ld+json'})
        if headscript:
            return _get_script_el(headscript.text,'isbn')
        else:
            return None
    

    def get_language(self) -> Optional[str]:
        '''returns language of loaded Goodreads book.'''
        self._confirm_loaded()
        headscript = self._soup.find('head').find('script',{'type': 'application/ld+json'})
        if headscript:
            return _get_script_el(headscript.text,'language')
        else:
            return None
    

    def get_image_url(self) -> Optional[str]:
        '''returns path to cover image of loaded Goodreads book.'''
        self._confirm_loaded()
        headscript = self._soup.find('head').find('script',{'type': 'application/ld+json'})
        if headscript:
            return _get_script_el(headscript.text,'pic_path')
        else:
            return None


    def get_description(self) -> Optional[str]:
        '''returns description of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        tc = self._info_main_metadat.find('div',class_='TruncatedContent')
        if tc:
            desc = tc.find('span',class_='Formatted')
            if desc:
                description = desc.text.strip()
                if not len(description):
                    description = None
        else:
            description = None
        return _rm_double_space(description)
    

    def get_rating(self) -> Optional[float]:
        '''returns average rating of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        b_r = self._info_main_metadat.find('div', class_='RatingStatistics__rating')
        return _check_soup(b_r,'convert to num')


    def get_rating_count(self) -> Optional[int]:
        '''returns number of ratings of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        r_c = self._info_main_metadat.find('span', {'data-testid': 'ratingsCount'})
        if r_c:
            rate_count = r_c.text.strip()
        else:
            rate_count = None
            return rate_count
        rate_count = re.sub(r'\,|\sratings|\srating','',rate_count)
        return int(rate_count) if len(rate_count) else rate_count
    

    def get_rating_dist(self) -> Optional[Dict[str,float]]:
        '''returns rating distribution of loaded Goodreads book.'''
        self._confirm_loaded()
        review_stats = self._soup.find('div',class_='RatingsHistogram RatingsHistogram__interactive')
        if not review_stats:
            return None
        rate_dist = {}
        tot_count = 0
        if review_stats:
            for button in review_stats.find_all('div',role='button')[::-1]:
                rating = re.sub(r'\sstars|\sstar','',button['aria-label'])
                count = button.find('div',class_='RatingsHistogram__labelTotal')
                count = re.sub(r'\(.*\)$|,','',count.text.strip())
                count = int(count)
                rate_dist[rating] = count
                
                tot_count += count
            if tot_count == 0:
                return None
            for stars,ct in rate_dist.items():
                rate_dist[stars] = round(ct / tot_count,2)
        return rate_dist


    def get_review_count(self) -> Optional[int]:
        '''returns numebr of reviews of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        r_c = self._info_main_metadat.find('span', {'data-testid': 'reviewsCount'})
        if r_c:
            rev_count = r_c.text.strip()
        else:
            rev_count = None
            return rev_count
        rev_count = re.sub(r'\,|\sreviews|\sreview','',rev_count)
        return int(rev_count) if len(rev_count) else rev_count


    def get_top_genres(self) -> Optional[List[str]]:
        '''returns top genres of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        g_l = self._info_main_metadat.find('ul',{'aria-label': 'Top genres for this book'})
        if g_l:
            top_genres = [
                i.find('span', class_ = 'Button__labelItem').text.strip()
                    for i 
                    in g_l.find_all('span', class_ = 'BookPageMetadataSection__genreButton')
                if len(i.find('span', class_ = 'Button__labelItem').text.strip())
            ]
        else:
            top_genres = None
        return top_genres
    

    def get_currently_reading(self) -> Optional[int]:
        '''returns number of users currently reading loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        c_r = self._info_main_metadat.find('div', {'data-testid': 'currentlyReadingSignal'})
        if c_r:
            cur_read = c_r.text.strip()
        else:
            cur_read = None
            return cur_read
        cur_read = re.sub(r'people.*$|person.*$','',cur_read)
        return int(cur_read) if len(cur_read) else cur_read


    def get_want_to_read(self) -> Optional[int]:
        '''returns number of users wanting to read loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._info_main_metadat:
            return None
        w_r = self._info_main_metadat.find('div', {'data-testid': 'toReadSignal'})
        if w_r:
            want_read = w_r.text.strip()
        else:
            want_read = None
            return want_read
        want_read = re.sub(r'people.*$|person.*$','',want_read)
        return int(want_read) if len(want_read) else want_read


    def get_page_length(self) -> Optional[int]:
        '''returns page length of loaded Goodreads book.'''
        self._confirm_loaded()
        if not self._details:
            return None
        p_l = self._details.find('p', {'data-testid': 'pagesFormat'})
        if p_l:
            page_length = p_l.text.strip()
            if not re.search(r'\d',page_length):
                return None   
        else:
            return None
        page_length = re.sub(r'pages.*$','',page_length)
        return int(page_length) if len(page_length) else page_length
    

    def get_first_published(self) -> Optional[str]:
        '''returns date ('DD/MM/YYYY') of when loaded Goodreads book was first published.'''
        self._confirm_loaded()
        if not self._details:
            return None
        f_p = self._details.find('p', {'data-testid': 'publicationInfo'})
        if f_p:
            first_pub = f_p.text.strip().lower()
            first_pub = re.sub(r'^.*published\s','',first_pub)
            try:
                date_grps = re.match(r'^([A-z][a-z]+) (\d+), (\d+)$', first_pub)
                if date_grps:
                    # if year published is < 1000
                    if len(date_grps.group(3)) < 4:
                        first_pub = f'{date_grps.group(1)} {date_grps.group(2)}, {date_grps.group(3).zfill(4)}'
                    first_pub = datetime.strptime(first_pub,'%B %d, %Y').strftime('%m/%d/%Y')
            except Exception:
                first_pub = None
        else:
            first_pub = None
            return first_pub
        return first_pub
    

    def get_similar_books(self) -> Optional[List[Dict[str,str]]]:
        '''returns list of books (with authors included) similar to loaded Goodreads book.'''
        self._confirm_loaded()
        bklst = self._soup.find('div', class_='BookDiscussions__list')
        if bklst:
            quote_url = bklst.find_all('a',class_='DiscussionCard')[0]['href'] # use this to get proper serial id
            similar_url = re.sub(r'work/quotes',r'book/similar',quote_url) # the serial id changes from main page to similar page
            similar_books = _get_similar_books(similar_url=similar_url)
        else:
            similar_books = []
        return similar_books
    

    async def get_similar_books_async(self,session) -> Optional[List[Dict[str,str]]]:
        '''returns list of books (with authors included) similar to loaded Goodreads book (ASYNC).'''
        self._confirm_loaded()
        bklst = self._soup.find('div', class_='BookDiscussions__list')
        if bklst:
            quote_url = bklst.find_all('a',class_='DiscussionCard')[0]['href'] # use this to get proper serial id
            similar_url = re.sub(r'work/quotes',r'book/similar',quote_url) # the serial id changes from main page to similar page
            similar_books = await _get_similar_books_async(session,similar_url)
        else:
            similar_books = None
        return similar_books
    

    def get_all_data(self,
                     exclude_attrs: Optional[List[str]] = ['similar_books'],
                     to_dict: bool = True) -> Union[Dict[str,Any],SimpleNamespace]:
        '''
        returns collection of data from loaded Goodreads book.

        :param exclude_attrs:
         list of book attributes to exclude. If None, collects all available attributes. See below for available book attributes.
        :param to_dict:
         if True, converts data collection to Dict format; otherwise, data is returned in SimpleNamespace format.
        
        ------------------------------------------------------------------------------
        returns the following available attributes:
        - **url** (str): URL to Goodreads book page
        - **id** (str): unique Goodreads book ID
        - **title** (str): book title
        - **author** (str): name of author of book
        - **author_id** (str): unique Goodreads author ID
        - **isbn** (str): ISBN code of book
        - **language** (str): language that book is in
        - **image_url** (str): URL to book's cover image
        - **description** (str): book description
        - **rating**: book's average rating (1-5)
        - **rating_distribution** (Dict[str,float]): book's rating's distribution; 
            - e.g., {'1': 0.02, '2': 0.06, '3': 0.24, '4': 0.42, '5': 0.25}
        - **rating_count** (int): number of user ratings given
        - **review_count** (int): number of user reviews given
        - **top_genres** (List[str]): list of top genres
            - e.g., ['Fiction', 'Historical Fiction', 'Alternate History']
        - **currently_reading** (int): number of Goodreads users currently reading the book
        - **want_to_read** (int): number of Goodreads users wanting to read the book
        - **page_length** (int): page length of book
        - **first_published** (str): book's initial publication date (in "MM/DD/YYYY" format)
        - **similar_books** (List[Dict]): list of similar books, with each element being a Dict of title/id/author_name
        '''
        self._confirm_loaded()
        attr_fn_map = {
            'url': lambda: self.book_url,
            'id': self.get_id,
            'title': self.get_title,
            'author': self.get_author_name,
            'author_id': self.get_author_id,
            'isbn': self.get_isbn,
            'language': self.get_language,
            'image_url': self.get_image_url,
            'description': self.get_description,
            'rating': self.get_rating,
            'rating_distribution': self.get_rating_dist,
            'rating_count': self.get_rating_count,
            'review_count': self.get_review_count,
            'top_genres': self.get_top_genres,
            'currently_reading': self.get_currently_reading,
            'want_to_read': self.get_want_to_read,
            'page_length': self.get_page_length,
            'first_published': self.get_first_published,
            'similar_books': self.get_similar_books
        }
        exclude_set = set(exclude_attrs) if exclude_attrs else set([])
        bk_dict = {}
        for attr,fn in attr_fn_map.items():
            if exclude_attrs:
                if attr not in exclude_set:
                    bk_dict[attr] = fn()
            else:
                bk_dict[attr] = fn()
        if not len(bk_dict):
            warnings.warn('Warning: returning empty object; param exclude_attrs should not include all attrs.') 
            return bk_dict if to_dict else SimpleNamespace()
        return bk_dict if to_dict else SimpleNamespace(**bk_dict)
    

    async def get_all_data_async(self,
                                 session: aiohttp.ClientSession,
                                 exclude_attrs: Optional[List[str]] = ['similar_books'],
                                 to_dict: bool = True) -> Union[Dict[str,Any],SimpleNamespace]:
        '''
        returns collection of data from loaded Goodreads book asynchronously.
        NB: should only be used if attempting to also pull 'similar_books'; use get_all_data otherwise

        :param session:
         an aiohttp.ClientSession object
        :param exclude_attrs:
         list of book attributes to exclude. If None, collects all available attributes. See below for available book attributes.
        :param to_dict:
         if True, converts data collection to Dict format; otherwise, data is returned in SimpleNamespace format.
        
        ------------------------------------------------------------------------------
        returns the following available attributes:
        - **url** (str): URL to Goodreads book page
        - **id** (str): unique Goodreads book ID
        - **title** (str): book title
        - **author** (str): name of author of book
        - **author_id** (str): unique Goodreads author ID
        - **isbn** (str): ISBN code of book
        - **language** (str): language that book is in
        - **image_url** (str): URL to book's cover image
        - **description** (str): book description
        - **rating**: book's average rating (1-5)
        - **rating_distribution** (Dict[str,float]): book's rating's distribution; 
            - e.g., {'1': 0.02, '2': 0.06, '3': 0.24, '4': 0.42, '5': 0.25}
        - **rating_count** (int): number of user ratings given
        - **review_count** (int): number of user reviews given
        - **top_genres** (List[str]): list of top genres
            - e.g., ['Fiction', 'Historical Fiction', 'Alternate History']
        - **currently_reading** (int): number of Goodreads users currently reading the book
        - **want_to_read** (int): number of Goodreads users wanting to read the book
        - **page_length** (int): page length of book
        - **first_published** (str): book's initial publication date (in "MM/DD/YYYY" format)
        - **similar_books** (List[Dict]): list of similar books, with each element being a Dict of title/id/author_name
        '''
        self._confirm_loaded()
        exclude_set = set(exclude_attrs) if exclude_attrs else set([])
        if 'similar_books' not in exclude_set:
            similar_books = await self.get_similar_books_async(session)
        else:
            similar_books = None
        
        attr_fn_map = {
            'url': lambda: self.book_url,
            'id': self.get_id,
            'title': self.get_title,
            'author': self.get_author_name,
            'author_id': self.get_author_id,
            'isbn': self.get_isbn,
            'language': self.get_language,
            'image_url': self.get_image_url,
            'description': self.get_description,
            'rating': self.get_rating,
            'rating_distribution': self.get_rating_dist,
            'rating_count': self.get_rating_count,
            'review_count': self.get_review_count,
            'top_genres': self.get_top_genres,
            'currently_reading': self.get_currently_reading,
            'want_to_read': self.get_want_to_read,
            'page_length': self.get_page_length,
            'first_published': self.get_first_published,
            'similar_books': lambda: similar_books if similar_books else None
        }
        
        bk_dict = {}
        for attr,fn in attr_fn_map.items():
            if exclude_attrs:
                if attr not in exclude_set:
                    bk_dict[attr] = fn()
            else:
                bk_dict[attr] = fn()
        if not len(bk_dict):
            warnings.warn('Warning: returning empty object; param exclude_attrs should not include all attrs.') 
            return bk_dict if to_dict else SimpleNamespace()
        return bk_dict if to_dict else SimpleNamespace(**bk_dict)
        
