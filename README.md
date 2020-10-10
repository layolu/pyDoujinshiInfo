# pyDoujinshiInfo
Unofficial Python3 REST API wrapper for [doujinshi.info](https://www.doujinshi.info/).  
Work in progress. In particular, the data structure may change significantly in the future.

## Install
If you're an adventurer, now you can install it with the following command from pypi:
```bash
$ pip install pyDoujinshiInfo
```
Or directly from the github repo:
```bash
$ pip install git+https://github.com/layolu/pyDoujinshiInfo
```

## Some of the usage
### Create an API instance with login
```python3
>>> from pyDoujinshiInfo import API
>>> api = API('your@email.address', 'your_password')
```
### Tags
#### get tag types
```python3
>>> tag_types = api.tag.types()
>>> tag_types
[{'id': 'J5KBm80mEPpr', 'name': {'japanese': '検閲', 'romaji': 'Kenetsu', 'english': 'Censoring'}, 'slug': 'censoring'}, {'id': 'PBRN40y60nZQ', 'name': {'japanese': 'キャラクター', 'romaji': 'Kyarakuta', 'english': 'Character'}, 'slug': 'character'}, {'id': 'lJyp4obm271L', 'name': {'japanese': 'サークル', 'romaji': 'Sakuru', 'english': 'Circle'}, 'slug': 'circle'}, {'id': 'Z3lAm5J4oyxg', 'name': {'japanese': 'コレクション', 'romaji': 'Korekushon', 'english': 'Collection'}, 'slug': 'collection'}, {'id': 'OMbP6nM4jYBn', 'name': {'japanese': 'コンテンツ', 'romaji': 'Kontentsu', 'english': 'Content'}, 'slug': 'content'}, {'id': 'LYAn4lL4Gljz', 'name': {'japanese': 'イベント', 'romaji': 'Ibento', 'english': 'Convention'}, 'slug': 'convention'}, {'id': 'oWYqmql9lJPj', 'name': {'japanese': 'シリーズ', 'romaji': 'Shirizu', 'english': 'Series'}, 'slug': 'series'}, {'id': 'JYB3my24XqGN', 'name': {'japanese': '作家', 'romaji': 'Sakka', 'english': 'Artist'}, 'slug': 'artist'}, {'id': 'R8AZ4G2mvWw2', 'name': {'japanese': '言語', 'romaji': 'Gengo', 'english': 'Language'}, 'slug': 'language'}]
>>> tag_types[1].id
'PBRN40y60nZQ'
>>> tag_types[1].slug
'character'
>>> tag_types[1].name.english
'Character'
>>> tag_types[1].name.japanese
'キャラクター'
```
#### get a specific tag with slug
```python3
>>> pmmm = api.tag.one('series', 'mahou-shoujo-madoka-magika')
# or shortly
>>> pmmm = api.tag('series', 'mahou-shoujo-madoka-magika')
>>> pmmm
<pyDoujinshiInfo.paginator.PaginatedResults object at 0x76834d50>
```
#### get basic data of the tag
```python3
>>> pmmm()
{'id': 'R8AZ4GRXmvWw', 'type': {'id': 'oWYqmql9lJPj', 'name': {'japanese': 'シリーズ', 'romaji': 'Shirizu', 'english': 'Series'}, 'slug': 'series'}, 'name': {'japanese': '魔法少女まどかマギカ', 'romaji': 'Mahou Shoujo Madoka Magika', 'english': 'Puella Magi Madoka Magica'}, 'slug': 'mahou-shoujo-madoka-magika', 'created_at': '2019-01-22 02:35:52', 'updated_at': '2019-01-22 02:35:52', 'tags': {'data': []}}
>>> pmmm().id
'R8AZ4GRXmvWw'
>>> pmmm().slug
'mahou-shoujo-madoka-magika'
>>> pmmm().name.japanese
'魔法少女まどかマギカ'
>>> pmmm().name.romaji
'Mahou Shoujo Madoka Magika'
>>> pmmm().name.english
'Puella Magi Madoka Magica'
```
#### get doujinshi list of the tag
##### total doujinshi count with that tag
```python3
>>> pmmm.total_num
1815
```
##### get 100 doujinshi data with that tag
results() returns a generator so iterable, but needs to be casted if you want a list
```python3
>>> books = list(pmmm.results(limit=100))
>>> len(books)
100
>>> books[99]
{'id': 'A7D9JdAyW4yX', 'name': {'japanese': '大事なものはあなただけ', 'romaji': 'Daiji Namonohaanatadake', 'english': None}, 'slug': 'daiji-namonohaanatadake', 'date_released': '2017-08-13', 'pages': 188, 'price': 1900, 'is_adult': False, 'is_copybook': False, 'is_anthology': False, 'is_novel': False, 'created_at': '2019-02-02 14:43:24', 'updated_at': '2019-04-17 19:08:17', 'cover': 'https://files.doujinshi.info/A7D9JdAyW4yX/2019-02-02/cover-HTKZ.jpg'}
>>> books[99].id
'A7D9JdAyW4yX'
>>> books[99].slug
'daiji-namonohaanatadake'
>>> books[99].name.japanese
'大事なものはあなただけ'
```
### Doujinshi
not written yet.

### Library 
not written yet.

## Official API docs
- [docs page](https://doujinshi-info.github.io/documentation/)
- [github repo](https://github.com/doujinshi-info/documentation)

