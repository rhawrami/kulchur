import aiohttp
import pytest

from kulchur import Pound


#########################
### LOADING FUNCTIONS ###
#########################

@pytest.mark.asyncio
@pytest.mark.parametrize(
    'author_id, expect_err', [
        ('128382', False), # Leo Tolstoy
        ('12806', False), # Hannah Arendt
        ('777777777', True) # nonexistent record
    ]
)
async def test_load_aio(author_id, expect_err):
    '''test if load_author_async works as intended'''
    async with aiohttp.ClientSession() as sesh:
        pnd = Pound()
        if expect_err:
            # for nonexistent records, ensure that err is raised
            with pytest.raises(Exception):
                await pnd.load_author_async(session=sesh, author_identifier=author_id)
            # for nonexistent ids, ensure that the author isn't loaded
            with pytest.raises(RuntimeError):
                pnd._confirm_loaded()
        else:
            await pnd.load_author_async(session=sesh, author_identifier=author_id)
            assert not pnd._confirm_loaded() # should return None in case that author is loaded


@pytest.mark.parametrize(
    'author_id, expect_err', [
        ('4644002', False), # Alexandre Kojeve
        ('21760712', False), # Wang Huning
        ('9999999', True), # nonexistent record
    ]
)
def test_load(author_id, expect_err):
    '''test if load_author works as intended'''
    pnd = Pound()
    if expect_err:
        with pytest.raises(Exception):
            pnd.load_author(author_identifier=author_id)
        with pytest.raises(RuntimeError):
            pnd._confirm_loaded()
    else:
        pnd.load_author(author_identifier=author_id)
        assert not pnd._confirm_loaded()

    
####################
### DATA PARSING ###
####################

@pytest.mark.parametrize(
    'author_id, name, b_date, d_date, bpl', [
        ('21559', 'Nassim Nicholas Taleb', None, None, 'Amioun, Lebanon'),
        ('879', 'Plato', None, None, 'Athens, Greece'),
        ('6819578', 'Augustine of Hippo', '11/07/0354', '08/22/0430', 'Thagaste, Numidia Cirtensis, Roman Empire'),
        ('17241', 'Michel de Montaigne', '06/13/1532', '09/13/1592', 'Guyenne, France')
    ]
)
def test_general_dat_parse(author_id, name, b_date, d_date, bpl):
    '''test parsing functions for general/static author data'''
    pnd = Pound()
    pnd.load_author(author_identifier=author_id)

    test_cfg = {
        pnd.get_name: name,
        pnd.get_birth_date: b_date,
        pnd.get_death_date: d_date,
        pnd.get_birth_place: bpl
    }

    for fn, expected in test_cfg.items():
        assert fn() == expected


@pytest.mark.parametrize(
    'author_id, book_sample_ids', [
        ('3873', ['117833', '229733', '4531917']),
        ('4785', ['7126', '10916717'])
    ]
)
def test_book_sample(author_id, book_sample_ids):
    '''test get_books_sample function'''
    pnd = Pound()
    pnd.load_author(author_identifier=author_id)

    bk_sample = pnd.get_books_sample()
    bk_ids = [bk['id'] for bk in bk_sample]

    for bk_id in book_sample_ids:
        assert bk_id in bk_ids


@pytest.mark.parametrize(
    'author_id, top_genres_sample', [
        ('1455', ['Fiction', 'Nonfiction', 'Classics']),
        ('1244', ['Short Stories', 'Biographies & Memoirs']),
        ('145435', ['Manga', 'Fantasy'])
    ]
)
def test_top_genres(author_id, top_genres_sample):
    '''test get_top_genres function'''
    pnd = Pound()
    pnd.load_author(author_identifier=author_id)

    for genre in top_genres_sample:
        assert genre in pnd.get_top_genres()


@pytest.mark.parametrize(
    'author_id, influences_sample', [
        ('30055', ['Dante Alighieri', 'John Milton', 'Confucius', 'Walt Whitman']),
        ('5031312', ['Plato', 'Virgil', 'Thomas Aquinas'])
    ]
)
def test_influences(author_id, influences_sample):
    '''test get_influences function'''
    pnd = Pound()
    pnd.load_author(author_identifier=author_id)

    influences = [a['author'] for a in pnd.get_influences()]

    for i in influences_sample:
        assert i in influences


@pytest.mark.parametrize(
    'author_id, rat, rat_n, rev_n, f_count', [
        ('5031312', 4.04, 450205, 22562, 6164),
        ('1127', 4.04, 104845, 5480, 1955)
    ]
)
def test_dynamic_dat_parse(author_id, rat, rat_n, rev_n, f_count):
    '''test parsing for dynamic data'''
    pnd = Pound()
    pnd.load_author(author_identifier=author_id)

    test_cfg = {
        pnd.get_rating: rat,
        pnd.get_rating_count: rat_n,
        pnd.get_review_count: rev_n,
        pnd.get_follower_count: f_count
    }

    for fn, expected in test_cfg.items():
        BE_WITHIN = .20
        diff = BE_WITHIN * expected
        lower, upper = expected - diff, expected + diff
        assert lower < fn() < upper


#########################
### BULK DATA PARSING ###
#########################

def test_bulk_dat_parse():
    '''test bulk data parsing'''
    AU_ID = '238' # use Joan Didion for testing
    pnd = Pound()
    pnd.load_author(author_identifier=AU_ID)

    dat_dict = pnd.get_all_data(to_dict=True) # dict
    dat_sns = pnd.get_all_data() # SimpleNamespace

    # basic tests
    assert dat_dict['name'] == 'Joan Didion'
    assert dat_sns.name == 'Joan Didion'

    assert 'Nonfiction' in dat_dict['top_genres']
    assert 'Nonfiction' in dat_sns.top_genres