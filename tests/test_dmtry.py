import time

import aiohttp
import pytest

from kulchur import FalseDmitry


#########################
### LOADING FUNCTIONS ###
#########################

@pytest.mark.asyncio
@pytest.mark.parametrize(
    'user_id, expect_err', [
        ('81541527', False), 
        ('45618', False), 
        ('777777777', True) # nonexistent record
    ]
)
async def test_load_aio(user_id, expect_err):
    '''test if load_user_async works as intended'''
    async with aiohttp.ClientSession() as sesh:
        dmtry = FalseDmitry()
        if expect_err:
            # for nonexistent records, ensure that err is raised
            with pytest.raises(Exception):
                await dmtry.load_user_async(session=sesh, user_identifier=user_id)
            # for nonexistent ids, ensure that the user isn't loaded
            with pytest.raises(RuntimeError):
                dmtry._confirm_loaded()
        else:
            await dmtry.load_user_async(session=sesh, user_identifier=user_id)
            assert not dmtry._confirm_loaded() # should return None in case that user is loaded


@pytest.mark.parametrize(
    'user_id, expect_err', [
        ('113964939', False), 
        ('128034500', False), 
        ('999999999', True), # nonexistent record
    ]
)
def test_load(user_id, expect_err):
    '''test if load_user works as intended'''
    dmtry = FalseDmitry()
    if expect_err:
        with pytest.raises(Exception):
            dmtry.load_user(user_identifier=user_id)
        with pytest.raises(RuntimeError):
            dmtry._confirm_loaded()
    else:
        dmtry.load_user(user_identifier=user_id)
        assert not dmtry._confirm_loaded()


####################
### DATA PARSING ###
####################
# for all following tests, use user 1, Otis Chandler (founder of Goodreads)

def test_numeric_data():
    '''test numeric data parsing functions'''
    dmtry = FalseDmitry()
    dmtry.load_user(user_identifier='1')
    
    test_cfg = {
        dmtry.get_rating: 4.19,
        dmtry.get_rating_count: 614,
        dmtry.get_review_count: 411,
        dmtry.get_friend_count: 2014,
        dmtry.get_follower_count: 115684
    }
    BE_WITHIN = .20

    for fn, expected in test_cfg.items():
        diff = BE_WITHIN * expected
        lower, upper = expected - diff, expected + diff
        assert lower < fn() < upper


def test_shelves():
    '''test get_shelf_names function'''
    shelves_sample = ['fantasy', 'spy', 'spiritual', 'programming', 'business']
    dmtry = FalseDmitry()
    dmtry.load_user(user_identifier='1')

    shelves = dmtry.get_shelf_names()
    for shelf in shelves_sample:
        assert shelf in shelves


def test_favorite_genres():
    '''test get_favorite_genres function'''
    dmtry = FalseDmitry()
    dmtry.load_user(user_identifier='1')

    fav_genres_sample = ['Crime', 'Business', 'technology', 'Fantasy']
    fav_genres = dmtry.get_favorite_genres()

    for fg in fav_genres_sample:
        assert fg in fav_genres


#########################
### BULK DATA PARSING ###
#########################

def test_bulk_parse():
    '''test get_all_data function'''
    dmtry = FalseDmitry()
    dmtry.load_user(user_identifier='1')

    d_dict = dmtry.get_all_data(to_dict=True)
    d_sns = dmtry.get_all_data()

    assert d_dict['name'] == 'Otis Chandler'
    assert d_sns.name == 'Otis Chandler'