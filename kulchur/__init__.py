'''
`kulchur` allows you to work with publicly available Goodreads data on books, authors and users (with public profiles).
You are able to get a number of different attributes for each of the three sources, from the ratings distribution for a book
to the author's birth place and birth date. You are also able to get the data asynchronously, allowing for pulling multiple
records in an official manner. Given the nature of this data, commercial use is not condoned or supported.
'''


__version__ = '1.0.0'


from .alexandria import Alexandria
from .pound import Pound
from .falsedmitry import FalseDmitry
from .insaneasylum import bulk_books_aio, bulk_authors_aio, bulk_users_aio


__all__ = [
    'Alexandria',
    'Pound',
    'FalseDmitry',
    'bulk_books_aio',
    'bulk_authors_aio',
    'bulk_users_aio'
]


