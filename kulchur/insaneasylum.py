import json
import time
import asyncio
from types import SimpleNamespace
from typing import (
    List, 
    Optional, 
    Dict, 
    Union,
    Any
)

import aiohttp

from .alexandria import Alexandria
from .falsedmitry import FalseDmitry
from .pound import Pound

# "All America is an insane asylum" - E.P.

async def _load_one_book_aio(session: aiohttp.ClientSession,
                             semaphore: asyncio.Semaphore,
                             identifer: str,
                             exclude_attrs: Optional[List[str]] = None,
                             num_attempts: int = 1,
                             see_progress: bool = True,
                             to_dict: bool = True) -> Optional[Union[SimpleNamespace,Dict,str]]:
            '''
            load one Goodreads book ASYNC
            
            :session: an aiohttp.ClientSession
            :semaphore: an asyncio.Semaphore
            :identifer: a book ID or URL
            :exclude_attrs: book attributes to exclude
            :num_attempts: number of attempts (including initial attempt)
            :see_progress: view progress for each book pull
            :to_dict: convert book data to dict; otherwise, stays SimpleNamespace
            '''
            async with semaphore:
                num_attempts = max(num_attempts, 1)
                for attempt in range(num_attempts):
                    try:
                        alx = Alexandria()
                        await alx.load_book_async(session=session,
                                                  book_identifier=identifer,
                                                  see_progress=see_progress)
                        if exclude_attrs and 'similar_books' in exclude_attrs:
                            bk_dat = alx.get_all_data(exclude_attrs=exclude_attrs,
                                                      to_dict=to_dict)
                        else:
                            bk_dat = await alx.get_all_data_async(session=session,
                                                                  exclude_attrs=exclude_attrs,
                                                                  to_dict=to_dict)
                        return bk_dat
                    
                    except asyncio.TimeoutError:
                        SLEEP_SCALAR = 1.5
                        sleep_time = (attempt + 1) ** SLEEP_SCALAR
                        await asyncio.sleep(sleep_time)
                        print(f'retrying {identifer} @ {time.ctime()}') if see_progress else None

                    except Exception as er:
                        print(er) if see_progress else None
                        return identifer         


async def _load_one_user_aio(session: aiohttp.ClientSession,
                             semaphore: asyncio.Semaphore,
                             identifer: str,
                             exclude_attrs: Optional[List[str]] = None,
                             num_attempts: int = 1,
                             see_progress: bool = True,
                             to_dict: bool = True) -> Optional[Union[SimpleNamespace,Dict]]:
            '''
            load one Goodreads user ASYNC
            
            :session: an aiohttp.ClientSession
            :semaphore: an asyncio.Semaphore
            :identifer: a user ID or URL
            :exclude_attrs: user attributes to exclude
            :num_attempts: number of attempts (including initial attempt)
            :see_progress: view progress for each user pull
            :to_dict: convert user data to dict; otherwise, stays SimpleNamespace
            '''
            async with semaphore:
                num_attempts = max(num_attempts, 1)
                for attempt in range(num_attempts):
                    try:
                        dmitry = FalseDmitry()
                        await dmitry.load_user_async(session=session,
                                                     user_identifier=identifer,
                                                     see_progress=see_progress)
                        usr_dat = dmitry.get_all_data(exclude_attrs=exclude_attrs,
                                                    to_dict=to_dict)
                        return usr_dat    
                
                    except asyncio.TimeoutError:
                        SLEEP_SCALAR = 1.5
                        sleep_time = (attempt + 1) ** SLEEP_SCALAR
                        await asyncio.sleep(sleep_time)
                        print(f'retrying {identifer} @ {time.ctime()}') if see_progress else None

                    except Exception as er:
                        print(er) if see_progress else None
                        return identifer         


async def _load_one_author_aio(session: aiohttp.ClientSession,
                               semaphore: asyncio.Semaphore,
                               identifer: str,
                               exclude_attrs: Optional[List[str]] = None,
                               num_attempts: int = 1,
                               see_progress: bool = True,
                               to_dict: bool = True) -> Optional[Union[SimpleNamespace,Dict]]:
            '''
            load one Goodreads author ASYNC
            
            :session: an aiohttp.ClientSession
            :semaphore: an asyncio.Semaphore
            :identifer: a author ID or URL
            :exclude_attrs: author attributes to exclude
            :num_attempts: number of attempts (including initial attempt)
            :see_progress: view progress for each author pull
            :to_dict: convert author data to dict; otherwise, stays SimpleNamespace
            '''
            async with semaphore:
                num_attempts = max(num_attempts, 1)
                for attempt in range(num_attempts):
                    try:
                        pnd = Pound()
                        await pnd.load_author_async(session=session,
                                                    author_identifier=identifer,
                                                    see_progress=see_progress)
                        authr_dat = pnd.get_all_data(exclude_attrs=exclude_attrs,
                                                    to_dict=to_dict)
                        return authr_dat
                
                    except asyncio.TimeoutError:
                        SLEEP_SCALAR = 1.5
                        sleep_time = (attempt + 1) ** SLEEP_SCALAR
                        await asyncio.sleep(sleep_time)
                        print(f'retrying {identifer} @ {time.ctime()}') if see_progress else None

                    except Exception as er:
                        print(er) if see_progress else None


async def bulk_load_aio(category: str,
                        identifiers: List[str],
                        exclude_attrs: Optional[List[str]] = None,
                        semaphore_count: int = 3,
                        num_attempts: int = 1,
                        batch_delay: Optional[int] = 1,
                        batch_size: Optional[int] = 5,
                        to_dict: bool = True,
                        see_progress: bool = True,
                        write_json: Optional[str] = None) -> List[Union[Dict[str, Any], SimpleNamespace]]:
    '''
    Collect multiple PUBLICLY AVAILABLE Goodreads units asynchronously.
    
    :param category: category to pull from; options include ['book', 'user', 'author']
    :param identifiers: unique item identifiers, or unique URLs
    :param exclude_attrs: item attributes to exclude
    :param semaphore_count: semaphore control; defaults to three requests
    :num_attempts: number of attempts (including initial attempt)
    :parm batch_delay: determines number of seconds to sleep per completion of each batch
    :param batch_size: determines batch size
    :param to_dict: converts data to dict type; otherwise, stays SimpleNamespace
    :param see_progress: view per-unit progress, such as notices of success/failure
    :param write_json: file_name to write data to json
    '''
    cat = category.lower()
    if cat not in ['book', 'user', 'author']:
         raise ValueError('category must be one of the three: ["book", "user", "author"]')
    
    cat_fn_map = {
        'book': _load_one_book_aio,
        'user': _load_one_user_aio,
        'author': _load_one_author_aio
    }
    cat_fn = cat_fn_map[category]
    
    sem = asyncio.Semaphore(semaphore_count)
    bulk_data = []
    failed_items = []
    async with aiohttp.ClientSession() as sesh:
        tasks = [cat_fn(session=sesh,
                        semaphore=sem,
                        identifer=id_,
                        exclude_attrs=exclude_attrs,
                        num_attempts=num_attempts,
                        see_progress=see_progress,
                        to_dict=to_dict) for id_ in identifiers]
        
        time_start = time.ctime()
        completed = 0
        async for item in asyncio.as_completed(tasks):
            if batch_delay and batch_size:
                 if completed > 0 and completed % batch_size == 0:
                      time.sleep(batch_delay)
            result = await item
            if isinstance(result,str):
                 failed_items.append(result)
            else:
                bulk_data.append(result)
            completed += 1
        time_end = time.ctime()
    
    attempted = len(identifiers)
    successes = len(bulk_data)
    failures = len(identifiers) - successes
    success_rate = successes / attempted
    if write_json:
        data_to_write = bulk_data if to_dict else [bk.__dict__ for bk in bulk_data]
        json_dat = {
            'category': cat,
            'query_start': time_start,
            'query_end': time_end,
            'attempted': attempted,
            'successes': successes,
            'failures': failures,
            f'{cat}s_failed': failed_items,
            'success_rate': success_rate,
            'results': data_to_write
        }
        with open(write_json,'w') as json_file:
            json.dump(json_dat,json_file,indent=4)

    metadat = f'''
------------------------------------
category: {cat}
started at: {time_start}
ended at: {time_end}
attempted: {attempted}
successes: {successes}
failures: {failures}
{cat}s failed: {failed_items}
success rate: {success_rate}
------------------------------------
'''
    print(metadat)

    return bulk_data
                        

async def bulk_books_aio(book_ids: List[str],
                         exclude_attrs: Optional[List[str]] = None,
                         semaphore_count: int = 3,
                         num_attempts: int = 1,
                         batch_delay: Optional[int] = None,
                         batch_size: Optional[int] = None,
                         to_dict: bool = True,
                         see_progress: bool = True,
                         write_json: Optional[str] = None) -> List[Union[Dict[str, Any], SimpleNamespace]]:
    '''
    Collect data on multiple PUBLICLY AVAILABLE Goodreads books asynchronously.
    
    :param book_ids: unique book identifiers, or book URLs
    :param exclude_attrs: book attributes to exclude; see below for options
    :param semaphore_count: semaphore control; defaults to three requests
    :num_attempts: number of attempts (including initial attempt)
    :parm batch_delay: determines number of seconds to sleep per completion of each batch
    :param batch_size: determines batch size
    :param to_dict: converts data to dict type; otherwise, stays SimpleNamespace
    :param see_progress: view per-book progress
    :param write_json: file_name to write data to json

    ------------------------------------------------------------------------------------------
    Data returned will by default include the following attributes:
    - **url** (str): URL to Goodreads book page
    - **id** (str): unique Goodreads book ID
    - **title** (str): book title
    - **author** (str): name of author of book
    - **author_id** (str): unique Goodreads author ID
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

    To override and exclude any of the attributes, include the attribute name in the 'exclude_attrs' param.
    - e.g., to exclude top_genres and author_id, set exclude_attrs = ['top_genres', 'author_id']
    '''
    return await bulk_load_aio(category='book',
                               identifiers=book_ids,
                               exclude_attrs=exclude_attrs,
                               semaphore_count=semaphore_count,
                               num_attempts=num_attempts,
                               batch_delay=batch_delay,
                               batch_size=batch_size,
                               to_dict=to_dict,
                               see_progress=see_progress,
                               write_json=write_json)


async def bulk_users_aio(user_ids: List[str],
                         exclude_attrs: Optional[List[str]] = None,
                         semaphore_count: int = 3,
                         num_attempts: int = 1,
                         batch_delay: Optional[int] = None,
                         batch_size: Optional[int] = None,
                         to_dict: bool = True,
                         see_progress: bool = True,
                         write_json: Optional[str] = None) -> List[Union[Dict[str, Any], SimpleNamespace]]:
    '''
    Collect data on multiple PUBLICLY AVAILABLE Goodreads users asynchronously.
    
    :param book_ids: unique user identifiers, or user URLs
    :param exclude_attrs: user attributes to exclude; see below for options
    :param semaphore_count: semaphore control; defaults to three requests
    :num_attempts: number of attempts (including initial attempt)
    :parm batch_delay: determines number of seconds to sleep per completion of each batch
    :param batch_size: determines batch size
    :param to_dict: converts data to dict type; otherwise, stays SimpleNamespace
    :param see_progress: view per-user progress
    :param write_json: file_name to write data to json

    ------------------------------------------------------------------------------------------
    returns the following available attributes:
    - **url** (str): URL to Goodreads user page
    - **id** (str): unique Goodreads user ID
    - **name** (str): user's name
    - **image_url** (str): URL to user's profile picture
    - **rating** (float): average of book ratings given by user (1-5)
    - **rating_count** (int): number of user ratings given
    - **review_count** (int): number of user reviews given
    - **favorite_genres** (List[str]): list of user's favorite genres
        - e.g., ['Fiction', 'Historical Fiction', 'Alternate History']
    - **currently_reading_sample** (List[Dict]): sample list of books that user is currently reading
    - **quotes_sample** (List[Dict]): sample list of quotes selected by user (note that this is dynamic)
    - **shelf_names** (List[str]): list of user's shelf names
    - **featured_shelf** (List[Dict]): user's featured shelf
    - **follower_count** (int): number of users that are following the loaded user
    - **friend_count** (int): number of users that user is friends with
    - **friends_sample** (List[Dict]): sample list of user's friends
    - **followings_sample** (List[Dict]): sample list of user's followings

    To override and exclude any of the attributes, include the attribute name in the 'exclude_attrs' param.
    - e.g., to exclude favorite_genres and friend_count, set exclude_attrs = ['favorite_genres', 'friend_count']
    '''
    return await bulk_load_aio(category='user',
                               identifiers=user_ids,
                               exclude_attrs=exclude_attrs,
                               semaphore_count=semaphore_count,
                               num_attempts=num_attempts,
                               batch_delay=batch_delay,
                               batch_size=batch_size,
                               to_dict=to_dict,
                               see_progress=see_progress,
                               write_json=write_json)


async def bulk_authors_aio(author_ids: List[str],
                           exclude_attrs: Optional[List[str]] = None,
                           semaphore_count: int = 3,
                           num_attempts: int = 1,
                           batch_delay: Optional[int] = None,
                           batch_size: Optional[int] = None,
                           to_dict: bool = True,
                           see_progress: bool = True,
                           write_json: Optional[str] = None):
    '''
    Collect data on multiple PUBLICLY AVAILABLE Goodreads authors asynchronously.
    
    :param author_ids: unique author identifiers, or author URLs
    :param exclude_attrs: author attributes to exclude; see below for options
    :param semaphore_count: semaphore control; defaults to three requests
    :num_attempts: number of attempts (including initial attempt)
    :parm batch_delay: determines number of seconds to sleep per completion of each batch
    :param batch_size: determines batch size
    :param to_dict: converts data to dict type; otherwise, stays SimpleNamespace
    :param see_progress: view per-author progress
    :param write_json: file_name to write data to json

    ------------------------------------------------------------------------------------------
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

    To override and exclude any of the attributes, include the attribute name in the 'exclude_attrs' param.
    - e.g., to exclude birth_place and influences, set exclude_attrs = ['birth_place', 'influences']
    '''
    return await bulk_load_aio(category='author',
                               identifiers=author_ids,
                               exclude_attrs=exclude_attrs,
                               semaphore_count=semaphore_count,
                               num_attempts=num_attempts,
                               batch_delay=batch_delay,
                               batch_size=batch_size,
                               to_dict=to_dict,
                               see_progress=see_progress,
                               write_json=write_json)
    
