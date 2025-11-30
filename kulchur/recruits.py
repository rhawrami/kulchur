import re
from typing import (
    List, 
    Optional, 
    Dict
)

import requests
import aiohttp
from bs4 import BeautifulSoup


def _check_soup(sp: Optional[BeautifulSoup],
                other_opr: Optional[str] = None) -> Optional[str]:
    '''
    checks if soup is empty; if not, returns text
    
    :sp: BeautifulSoup object
    :other_opr: other string operation; currently only takes 'convert to num'
    '''
    if sp:
        s = sp.text.strip()
        if other_opr:
            if other_opr == 'convert to num':
                s = float(s)
    else:
        s = None
    return s


def _get_script_el(script: str,
                   res_el: str) -> Optional[str]:
    '''
    parses header script, returns desired element
    
    :script: Goodreads book header script
    :res_el: resulting element; currently accepts ['isbn', 'language', 'pic_path']
    '''
    elements = re.sub(r'\'|\"','',script).split(',')
    if res_el == 'isbn':
        sub = r'^isbn\:'
    elif res_el == 'language':
        sub = r'^inLanguage\:'
    elif res_el == 'pic_path':
        sub = r'^image\:'
    res = None
    for el in elements:
        if re.search(sub,el):
            res = re.sub(sub,'',el)
    return res


def _parse_id(url: str) -> Optional[str]:
    '''
    parses Goodreads book/author/user url for unique ID,returns ID string
    
    :url: book/author/user url
    '''
    id_ = re.findall(r'\d+',url)
    if len(id_):
        return id_[0]
    else:
        return None


def _get_similar_books(similar_url: str) -> Optional[List[Dict[str,str]]]:
    '''
    returns similar book data for a given book

    :similar_url: original GoodReads book url 

    Returns list of dictionaries of similar books, of the form:\n
    [{'book': BOOK_TITLE, 'url': book_identifier, 'author': BOOK_AUTHOR},...]
    '''
    try:
        r = requests.get(similar_url)
        soup = BeautifulSoup(r.text,'lxml')
        dat = []
        bklist = soup.find_all('div',class_='responsiveBook')

        if not bklist:
            return None
        
        for idx,book in enumerate(bklist):
            if idx == 0:
                continue # this is the original book
            else:
                b_url = 'https://www.goodreads.com' + book.find('a',itemprop='url')['href']
                b_id = _parse_id(b_url)
                b_title = book.find_all('span',itemprop='name')[0].text.strip()
                b_author = book.find_all('span',itemprop='name')[1].text.strip()
                dat.append({
                    'id': b_id,
                    'title': b_title,
                    'author': b_author
                })
        return dat if len(dat) else None

    except requests.HTTPError as er:
        print(er)
        return None
    except Exception as er:
        print(er)
        return None


async def _get_similar_books_async(session: aiohttp.ClientSession,
                                   similar_url: str) -> Optional[List[Dict[str,str]]]:
    '''
    ASYNC returns similar book data for a given book

    :similar_url: original GoodReads book url 

    Returns list of dictionaries of similar books, of the form:\n
    [{'book': BOOK_TITLE, 'title': book_identifier, 'author': BOOK_AUTHOR},...]
    '''
    try:
        async with session.get(similar_url) as resp:
            text = await resp.text()
            soup = BeautifulSoup(text,'lxml')
            dat = []
            for idx,book in enumerate(soup.find_all('div',class_='responsiveBook')):
                if idx == 0:
                    continue # this is the original book
                else:
                    b_url = 'https://www.goodreads.com' + book.find('a',itemprop='url')['href']
                    b_id = _parse_id(b_url)
                    b_title = book.find_all('span',itemprop='name')[0].text.strip()
                    b_author = book.find_all('span',itemprop='name')[1].text.strip()
                    dat.append({
                        'id': b_id,
                        'title': b_title,
                        'author': b_author
                    })
            return dat if len(dat) else None
    except aiohttp.ClientError as er:
        print(er)
        return None
    except Exception as er:
        print(er)
        return None
    

def _get_user_stat(txt: str, 
                   st_type: str) -> Optional[int]:
    '''
    returns number of ratings, or ratings average
    
    :txt: text string
    :st_type: text string type; current options are ['num_ratings', 'avg_ratings', 'num_reviews']
    '''
    if st_type == 'num_ratings':
        sub_pattern = r'\sratings|\srating'
    elif st_type == 'avg_ratings':
        sub_pattern = r' avg|\(|\)'
    elif st_type == 'num_reviews':
        sub_pattern = r'\sreviews|\sreview'
    else:
        return None
    
    cleaned_txt = re.sub(sub_pattern,'',txt)
    try:
        int_text = int(cleaned_txt) if '.' not in cleaned_txt else float(cleaned_txt)
    except ValueError:
        int_text = None
    return int_text


def _rm_double_space(txt: str) -> Optional[str]:
    '''
    returns string stripped of consecutive double (or more) spaces
    
    :txt: text string
    '''
    if not isinstance(txt, str):
        return None
    return re.sub(r'\s+', ' ', txt)