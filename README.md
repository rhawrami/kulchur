# kulchur
Pull publicly available Goodreads data on books, authors and users.

<img src="./img/klchr.png" width="350"/>

## description
`kulchur` is a python package that allows you to work with publicly available Goodreads data on books, authors and users (with public profiles).
You are able to get a number of different attributes for each of the three sources, from the ratings distribution for a book
to the author's birth place and birth date. You are also able to get the data asynchronously, allowing for pulling multiple
records in an official manner. **Given the nature of this data, commercial use is not condoned or supported.**

## installation
You can install `kulchur` via PyPi:
```bash
$ pip install kulchur
```

## usage
`kulchur` allows you to pull data on publicly available books, authors, and users on Goodreads. There are three classes, one for each
data source:

- `Alexandria` for book data
- `Pound` for author data
- `FalseDmitry` for user data

Each class requires either
- the unique Goodreads ID for an item; for example, the ID for Ivan Turgenev is `410680`, found in [the URL](https://www.goodreads.com/author/show/410680.Ivan_Turgenev) of Turgenev's page.
- the URL to a[n] author/book/user's page.

### loading the data
After initializing one of the three classes, you can now load the data, either asynchronously or non-asynchronously:

```python
alx = Alexandria()

# asynchronously
with aiohttp.ClientSession() as sesh:
    await alx.load_book_async(session=sesh, 
                              book_identifier='410680')

# regularly
alx.load_book(book_identifier='410680')
```

Errors will occur when a non-200 response is recieved, such as when an item is non-existent. Further, when pulling user data, an 
error will be returned if a user is private.

### pulling specific fields
Each of the three classes have a number of methods for pulling specific fields after initially loading in the data, all starting with `get`. See below for a handful of examples for each:
```python
# book data
alx = Alexandria()
alx.get_title() # returns title name
alx.get_top_genres() # returns list of book's genres
alx.get_rating_dist() # returns rating-share dictionary, e.g., {'1': .2, '2': .4,..., '5': .05} 

# author data
pnd = Pound()
pnd.get_review_count() # returns number of user reviews submitted
pnd.get_quotes_sample() # returns sample (n=3) of quotes by author
pnd.get_birth_place() # returns author's birthplace

# user data
dmtry = FalseDmitry()
dmtry.get_favorite_genres() # returns list of author's favorite genres
dmtry.get_follower_count() # returns user's number of followers
dmtry.get_name() # returns user name
```

In cases where the field is not available, `None` will be returned

### pulling fields in bulk
Each of the three classes all have bulk data methods, each called
`get_all_data()`. You can pass attributes you want to exclude, and whether
you want a dictionary or SimpleNamespace format:
```python
alx = Alexandria()
dat = alx.get_all_data(exclude_attrs=['rating', 'similar_books'],
                       to_dict=True)
```

### pulling multiple items
If you'd like to pull more than one item at a time, you can use the
`load_[item]_aio` functions for asynchronous pulls. The functions have a number of configurations avaialable, from JSON exports to semaphore counts to number of attempts per pull:
```python
# pull book data on 
#   Fathers and Sons by Ivan Turgenev
#   The Master and Margarita by Mikhail Bulgakov
#   The Year of Magical Thinking by Joan Didion
dat = await bulk_books_aio(book_ids=['19117', '117833', '7815'],
                           exclude_attrs=['similar_books'],
                           semaphore_count=2,
                           batch_delay=None,
                           batch_size=None,
                           to_dict=True,
                           see_progress=True,
                           write_json='out_books.json')
```
Try to be considerate of Goodreads server load. And again, **given the nature of this data, commercial use is not condoned or supported.**