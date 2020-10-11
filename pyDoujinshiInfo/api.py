from datetime import datetime, timedelta
from typing import BinaryIO, Dict, List, Optional, Type
import jwt
from tortilla import wrap
from tortilla.cache import BaseCache, DictCache
from tortilla.utils import Bunch, bunchify
from .paginator import PaginatedResults
from .utils import tag_list_to_dict


class API:
    ENDPOINT = 'https://api.doujinshi.info/v1/'

    def __init__(self, email='', password='', refresh_deadline_sec=30,
                 tortilla_debug=False, tortilla_cache: Type[BaseCache] = DictCache(),
                 tortilla_cache_lifetime: Optional[int] = None) -> None:
        self.root = wrap(self.ENDPOINT, cache=tortilla_cache, cache_lifetime=tortilla_cache_lifetime,
                         debug=tortilla_debug)
        self.refresh_deadline_sec = refresh_deadline_sec
        self.access_token = ''
        self.refresh_token = ''
        self.me = Bunch()
        self.expires_at: Optional[datetime] = None

        self.auth = Auth(self)
        self.tag = Tag(self)
        self.doujinshi = Doujinshi(self)
        self.changelog = Changelog(self)
        self.user = User(self)
        self.library = Library(self)
        self.following = Following(self)
        self.notifications = Notifications(self)

        if email and password:
            self.auth.login(email, password)


class Part:
    def __init__(self, api: API) -> None:
        self._api = api
        self.root = api.root


class Auth(Part):
    def __init__(self, api: API) -> None:
        super().__init__(api)
        self.auth = api.root.auth

    def set_access_token(self, access_token: str) -> None:
        self._api.access_token = access_token
        self.root.config['headers']['Authorization'] = 'Bearer {}'.format(access_token)
        self._api.me = bunchify(jwt.decode(access_token, verify=False))
        self._api.expires_at = datetime.fromtimestamp(self._api.me.exp)

    def register(self, name: str, email: str, password: str, password_confirmation: str) -> None:
        res: Bunch = self.auth.create.post(params={
            'name': name, 'email': email, 'password': password, 'password_confirmation': password_confirmation
        })
        self.set_access_token(res.access_token)
        self._api.refresh_token = res.refresh_token

    def login(self, email: str, password: str) -> None:
        res: Bunch = self.auth.login.post(params={
            'email': email, 'password': password
        })
        self.set_access_token(res.access_token)
        self._api.refresh_token = res.refresh_token

    def refresh(self) -> None:
        # If the time remaining before the expiration time 
        # is less than a set number of seconds (default: 30 seconds), update the token.
        if not self._api.expires_at or \
                (self._api.expires_at - datetime.now()) < \
                timedelta(seconds=self._api.refresh_deadline_sec):
            res: Bunch = self.root.auth.login.post(params={
                'user': self._api.me.sub, 'refresh_token': self._api.refresh_token
            }, cache_lifetime=None)
            self.set_access_token(res.access_token)
        else:
            pass


class Tag(Part):
    def __init__(self, api: API) -> None:
        super().__init__(api)
        self.tag = api.root.tag

    def types(self) -> Bunch:
        return self.tag.types.get().data

    def all(self, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.tag.get, params={'page': page, 'limit': limit})

    def by_type(self, tag_type: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.tag(tag_type).get, params={'page': page, 'limit': limit})

    def one(self, tag_type: str, slug: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.tag(tag_type)(slug).get, paginated_key='books',
                         params={'page': page, 'limit': limit})

    __call__ = one

    def changelog(self, tag_type: str, slug: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.tag(tag_type)(slug).changelog.get, params={'page': page, 'limit': limit})

    def create(self, type: str, name_japanese: str, tags: List[str] = [], **kwargs: str) -> PaginatedResults:
        data = {'type': type, 'name_japanese': name_japanese}
        for key in ('name_romaji', 'name_english', 'aliases', 'description_english',
                    'description_japanese', 'date_start', 'date_end', 'links'):
            if key in kwargs:
                data[key] = kwargs[key]
        self._api.auth.refresh()
        return PaginatedResults(self.tag.post, paginated_key='books', data=data)

    def update(self, tag_type: str, slug: str, name_japanese: str, tags: List[str] = [],
               **kwargs: str) -> PaginatedResults:
        data = {'name_japanese': name_japanese}
        for key in ('name_romaji', 'name_english', 'aliases', 'description_english',
                    'description_japanese', 'date_start', 'date_end', 'links'):
            if key in kwargs:
                data[key] = kwargs[key]
        self._api.auth.refresh()
        return PaginatedResults(self.tag(tag_type)(slug).put, paginated_key='books', data=data)

    def search(self, tag_type: str, query: str, page=1, limit=24) -> PaginatedResults:
        params = {'q': query, 'page': page, 'limit': limit}
        return PaginatedResults(self.root.search.tag(tag_type).get, params=params)


class Doujinshi(Part):
    def __init__(self, api: API) -> None:
        super().__init__(api)
        self.book = api.root.book

    def all(self, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.book.get, params={'page': page, 'limit': limit})

    def one(self, slug: str) -> Bunch:
        return self.book(slug).get()

    __call__ = one

    def changelog(self, slug: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.book(slug).changelog.get, params={'page': page, 'limit': limit})

    def create(self, name_japanese: str, tag_ids: List[str] = [], links: Optional[Dict[str, str]] = {},
               cover: Optional[BinaryIO] = None, samples: Optional[List[BinaryIO]] = [], **kwargs: str) -> Bunch:
        data = {'name_japanese': name_japanese}
        data.update(tag_list_to_dict(tag_ids))
        for key in ('name_romaji', 'name_english', 'date_released', 'pages', 'price',
                    'is_copybook', 'is_anthology', 'is_adult', 'is_novel', 'links'):
            if key in kwargs:
                data[key] = str(kwargs[key])
        if links:
            for site_name, url in links.items():
                data['links[{}]'.format(site_name)] = url

        files = []
        if cover:
            files.append(('cover', cover))
        if samples:
            sample: BinaryIO
            for i, sample in enumerate(samples):
                files.append(('samples[{}]'.format(i), sample))
        self._api.auth.refresh()
        return self.book.post(data=data, files=files, format=(None, 'json'))

    def update(self, slug: str, name_japanese: str, tag_ids: List[str] = [], links: Optional[Dict[str, str]] = {},
               cover: Optional[BinaryIO] = None, samples: Optional[List[BinaryIO]] = None, **kwargs: str) -> Bunch:
        # TODO: Is the parameter name_japanese really mandatory when updating?
        data = {'name_japanese': name_japanese, 'tags': tag_ids}
        data.update(tag_list_to_dict(tag_ids))
        # Warning, this completely REPLACES old tag list,
        # so if you want simply add or remove tags, use methods below
        # data.update(tag_list_to_dict(tag_ids))
        for key in ('name_romaji', 'name_english', 'date_released', 'pages', 'price',
                    'is_copybook', 'is_anthology', 'is_adult', 'is_novel', 'links'):
            if key in kwargs:
                data[key] = kwargs[key]
        if links:
            for site_name, url in links.items():
                data['links[{}]'.format(site_name)] = url

        files = []
        if cover:
            files.append(('cover', cover))
        if samples:
            # files['samples']: samples
            # files.append(('samples', samples))
            sample: BinaryIO
            for i, sample in enumerate(samples):
                files.append(('samples[{}]'.format(i), sample))
        print(files)
        self._api.auth.refresh()
        return self.book(slug).post(data=data, files=files, format=(None, 'json'))

    def add_tags(self, slug: str, tag_ids: List[str] = []) -> Bunch:
        # TODO WIP
        doujinshi = self.one(slug)
        new_ids = list(set([tag.id for tag in doujinshi.tags.data] + tag_ids))
        return self.update(slug, doujinshi.name.japanese, new_ids)

    def import_url(self, url: str) -> Bunch:
        self._api.auth.refresh()
        return self.root('import').post(data={'url': url})

    def search(self, query: str, page=1, limit=24, **kwargs: str) -> PaginatedResults:
        # TODO: boolean params actually takes 0 or 1
        params = {'q': query, 'page': page, 'limit': limit}
        for key in ('copybook', 'anthology', 'adult', 'novel'):
            if key in kwargs:
                params[key] = kwargs[key]
        return PaginatedResults(self.root.search.get, params=params)

    def image_search(self, image, page=1, limit=24):
        files = {'image': image}
        params = {'page': page, 'limit': limit}
        self._api.auth.refresh()
        return PaginatedResults(self.root.search.image.post, files=files, params=params)


class Changelog(Part):
    def __init__(self, api: API) -> None:
        super().__init__(api)
        self.changelog = self.root.changelog

    def all(self, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.changelog.get, params={'page': page, 'limit': limit})

    def one(self, id_: str) -> Bunch:
        return self.changelog(id_).get()

    __call__ = one


class User(Part):
    def __init__(self, api: API) -> None:
        super().__init__(api)
        self.user = self.root.user

    def one(self, slug: str) -> Bunch:
        return self.user(slug).get()

    __call__ = one

    def contributions(self, slug: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.user(slug).contributions.get, params={'page': page, 'limit': limit})

    # def update_settings(self):
    #    pass

    def library(self, slug: str, lib_type: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self.user(slug).library(lib_type).get, params={'page': page, 'limit': limit})

    def following(self, slug: str, page=1, limit=24) -> PaginatedResults:
        self._api.auth.refresh()
        return PaginatedResults(self.user(slug).following.get, params={'page': page, 'limit': limit})


class Library(Part):
    def __init__(self, api: API) -> None:
        super().__init__(api)
        self.library = self.root.library

    def check(self, lib_type: str, book_id: str) -> bool:
        self._api.auth.refresh()
        return self.library(lib_type)(book_id).get().data

    def add(self, lib_type: str, book_id: str) -> None:
        self._api.auth.refresh()
        self.library(lib_type).post(data={'book': book_id})

    def remove(self, lib_type: str, book_id: str) -> None:
        self._api.auth.refresh()
        self.library(lib_type).delete(data={'book': book_id})


class Following(Part):
    def __init__(self, api: API) -> None:
        super().__init__(api)
        self.following = self.root.following

    def check(self, tag_id: str) -> bool:
        self._api.auth.refresh()
        return self.following(tag_id).get().data

    def follow(self, tag_id: str) -> None:
        self._api.auth.refresh()
        self.following.post(data={'tag': tag_id})

    def unfollow(self, tag_id: str) -> None:
        self._api.auth.refresh()
        self.following.delete(data={'tag': tag_id})


class Notifications(Part):
    def __init__(self, api: API) -> None:
        super().__init__(api)
        self.notifications = self.root.notifications

    def all(self, page=1, limit=24) -> PaginatedResults:
        self._api.auth.refresh()
        return PaginatedResults(self.notifications.get, params={'page': page, 'limit': limit})

    __call__ = all

    def unread_count(self) -> int:
        self._api.auth.refresh()
        return self.notifications.count.get().data

    def mark_as_read(self, notification_id: str) -> Bunch:
        self._api.auth.refresh()
        return self.notifications.read.put(data={'notification': notification_id}).data

    def mark_all_as_read(self) -> Bunch:
        self._api.auth.refresh()
        return self.notifications.read.all.put().data
