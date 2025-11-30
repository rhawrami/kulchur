import pytest

from kulchur import bulk_books_aio, bulk_authors_aio, bulk_users_aio


@pytest.mark.asyncio
async def test_bulk_books_aio():
    '''test bulk_books_aio function'''
    TEST_CFG = {
        '19117': {
            'title': 'Fathers and Sons',
            'author': 'Ivan Turgenev',
            'top_genres_sample': ['Fiction', 'Russia', 'Classics']
        },
        '7784': {
            'title': 'The Lorax',
            'author': 'Dr. Seuss',
            'top_genres_sample': ['Childrens', 'Poetry', 'Picture Books']
        },
        '675877': {
            'title': 'Mirror of the Intellect: Essays on the Traditional Science and Sacred Art',
            'author': 'Titus Burckhardt',
            'top_genres_sample': ['Philosophy', 'Religion', 'Metaphysics']
        }
    }
    bk_ids = [id_ for id_ in TEST_CFG.keys()]
    dat = await bulk_books_aio(book_ids=bk_ids, 
                               to_dict=True,
                               semaphore_count=2)

    for bk in dat:
        bk_id = bk['id']
        assert bk['title'] == TEST_CFG[bk_id]['title']
        assert bk['author'] == TEST_CFG[bk_id]['author']
        for genre in TEST_CFG[bk_id]['top_genres_sample']:
            assert genre in bk['top_genres']


@pytest.mark.asyncio
async def test_bulk_authors_aio():
    '''test bulk_authors_aio function'''
    TEST_CFG = {
        '112858': {
            'name': 'Titus Burckhardt',
            'bpl': 'Florence, Italy',
            'top_genres_sample': None
        },
        '941441': {
            'name': 'Stephenie Meyer',
            'bpl': 'Connecticut, The United States',
            'top_genres_sample': ['Paranormal Romance', 'Young Adult']
        },
        '5144': {
            'name': 'James Joyce',
            'bpl': 'Rathgar, Dublin, Ireland',
            'top_genres_sample': ['Fiction', 'Poetry']
        }
    }

    au_ids = [id_ for id_ in TEST_CFG.keys()]
    dat = await bulk_authors_aio(author_ids=au_ids, 
                                 to_dict=True,
                                 semaphore_count=2)
    
    for au in dat:
        au_id = au['id']
        assert au['name'] == TEST_CFG[au_id]['name']
        assert au['birth_place'] == TEST_CFG[au_id]['bpl']
        if not TEST_CFG[au_id]['top_genres_sample']:
            assert not au['top_genres']
        else:
            for genre in TEST_CFG[au_id]['top_genres_sample']:
                assert genre in au['top_genres']


@pytest.mark.asyncio
async def test_bulk_users_aio():
    '''test bulk_users_aio function'''
    TEST_CFG = {
        '1': {
            'name': 'Otis Chandler',
            'favorite_genres_sample': ['Biography', 'Business']
        },
        '8114361': {
            'name': 'Jesse (JesseTheReader)',
            'favorite_genres_sample': ['Comics', 'Fantasy']
        },
        '3030788': {
            'name': 'Melanie (meltotheany)',
            'favorite_genres_sample': ['Adult Fiction', 'Fantasy']
        }
    }

    usr_ids = [id_ for id_ in TEST_CFG.keys()]
    dat = await bulk_users_aio(user_ids=usr_ids,
                               to_dict=True,
                               semaphore_count=2)
    
    for usr in dat:
        usr_id = usr['id']
        assert usr['name'] == TEST_CFG[usr_id]['name']
        for genre in TEST_CFG[usr_id]['favorite_genres_sample']:
            assert genre in usr['favorite_genres']