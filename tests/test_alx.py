import time

import aiohttp
import pytest

from kulchur import Alexandria


#########################
### LOADING FUNCTIONS ###
#########################

@pytest.mark.asyncio
@pytest.mark.parametrize(
    'book_id, expect_err', [
        ('7144', False), # Crime and Punishment
        ('41865', False), # Twilight
        ('93928239', True) # nonexistent record
    ]
)
async def test_load_aio(book_id, expect_err):
    '''test if load_book_async works as intended'''
    async with aiohttp.ClientSession() as sesh:
        alx = Alexandria()
        if expect_err:
            # for nonexistent records, ensure that err is raised
            with pytest.raises(Exception):
                await alx.load_book_async(session=sesh, book_identifier=book_id)
            # for nonexistent ids, ensure that the book isn't loaded
            with pytest.raises(RuntimeError):
                alx._confirm_loaded()
        else:
            await alx.load_book_async(session=sesh, book_identifier=book_id)
            assert not alx._confirm_loaded() # should return None in case that book is loaded


@pytest.mark.parametrize(
    'book_id, expect_err', [
        ('8423489', True), # nonexistent record
        ('39102013', True), # nonexistent record
        ('12395', False), # Journey to the End of the Night
        ('176444106', False) # Abundance
    ]
)
def test_load(book_id, expect_err):
    '''test if load_book works as intended'''
    alx = Alexandria()
    if expect_err:
        with pytest.raises(Exception):
            alx.load_book(book_identifier=book_id)
        with pytest.raises(RuntimeError):
            alx._confirm_loaded()
    else:
        alx.load_book(book_identifier=book_id)
        assert not alx._confirm_loaded()


####################
### DATA PARSING ###
####################

@pytest.mark.parametrize(
    'book_id, title, author_name, author_id, lang, first_pub, page_len', [
        ('176444106', 'Abundance', 'Ezra Klein', '4412018', 'English', '03/18/2025', 304), # Abundance
        ('113205', 'Heart of a Dog', 'Mikhail Bulgakov', '3873', 'English', '01/01/1925', 123), # Heart of a Dog
        ('675877', 'Mirror of the Intellect: Essays on the Traditional Science and Sacred Art', 'Titus Burckhardt', '112858', 'English', '01/01/1987', 269) # Mirror of the Intellect
    ]
)
def test_general_datparse(book_id, 
                          title, 
                          author_name,
                          author_id,
                          lang,
                          first_pub,
                          page_len):
    '''test parsing functions for general/descriptive static data'''
    alx = Alexandria()
    alx.load_book(book_identifier=book_id)
    
    test_cfg = {
        alx.get_title: title,
        alx.get_author_name: author_name,
        alx.get_author_id: author_id,
        alx.get_language: lang,
        alx.get_first_published: first_pub,
        alx.get_page_length: page_len
    }

    for fn, expected in test_cfg.items():
        assert fn() == expected


@pytest.mark.parametrize(
    'book_id, rat, n_rat, n_rev, n_want, n_cur', [
        ('19510', 4.16, 8997, 430, 22682, 756), # Essays and Aphorisms
        ('84737', 3.77, 32057, 1637, 38112, 2944) # Zeno's Conscience
    ]
)
def test_dynamic_datparse(book_id,
                          rat,
                          n_rat,
                          n_rev,
                          n_want,
                          n_cur):
    '''test parsing functions for dynamic data'''
    alx = Alexandria()
    alx.load_book(book_identifier=book_id)

    # Given that these numbers (like rating count) change over time, we'll just ensure that 
    # the returned data be within a range of values; specifically, within 20% of the true value.
    # This'll make future tests more stable as well.
    BE_WITHIN = .20

    test_cfg = {
        alx.get_rating: rat,
        alx.get_rating_count: n_rat,
        alx.get_review_count: n_rev,
        alx.get_want_to_read: n_want,
        alx.get_currently_reading: n_cur
    }

    for fn, expected in test_cfg.items():
        diff = expected * BE_WITHIN
        lower, upper = expected - diff, expected + diff
        assert lower < fn() < upper


@pytest.mark.parametrize(
    'book_id, genre_sample', [
        ('7815', ['Nonfiction', 'Memoir', 'Grief']), # The Year of Magical Thinking
        ('248871', ['Manga', 'Fantasy', 'Horror', 'Seinen']), # Berserk (Vol. 1)
        ('18386', ['Classics', 'Short Stories', 'Russia']) # The Death of Ivan Ilych
    ]
)
def test_genre_parse(book_id, genre_sample):
    '''test genre parsing'''
    alx = Alexandria()
    alx.load_book(book_identifier=book_id)

    genres = alx.get_top_genres()
    for genre in genre_sample:
        assert genre in genres


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'book_id, sim_book_entries_sample', [
        (
            # Notes From Underground
            '49455', [
                {'id': '17690', 'title': 'The Trial', 'author': 'Franz Kafka'},
                {'id': '19117', 'title': 'Fathers and Sons', 'author': 'Ivan Turgenev'}
            ]
        ),
        (
            # Demons
            '5695', [
                {'id': '28381', 'title': 'Dead Souls', 'author': 'Nikolai Gogol'},
                {'id': '656', 'title': 'War and Peace', 'author': 'Leo Tolstoy'}
            ]
        )
    ]
)
async def test_sim_books_parse(book_id, sim_book_entries_sample):
    '''test get_similar_books'''
    # since the async and the non-async version are essentially the same, we'll just
    # test the async version
    async with aiohttp.ClientSession() as sesh:
        alx = Alexandria()
        await alx.load_book_async(session=sesh, book_identifier=book_id)
        time.sleep(3) # prevent timeout
        sim_books = await alx.get_similar_books_async(session=sesh)
    
    for sim_bk in sim_book_entries_sample:
        assert sim_bk in sim_books


#########################
### BULK DATA PARSING ###
#########################

def test_bulk_dat_parse():
    # use Moby Dick
    BOOK_ID = '153747'
    alx = Alexandria()
    alx.load_book(book_identifier=BOOK_ID)
    time.sleep(3) # prevent timeout

    d_dict = alx.get_all_data(to_dict=True) # dictionary format of bulk data
    time.sleep(3) 
    d_ns = alx.get_all_data() # SimpleNamespace format

    # basic checks now
    # author
    assert d_dict['author'] == 'Herman Melville'
    assert d_ns.author == 'Herman Melville'
    # language
    assert d_dict['language'] == 'English'
    assert d_ns.language == 'English'
    

