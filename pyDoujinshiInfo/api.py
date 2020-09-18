from datetime import datetime, timedelta
from typing import BinaryIO, Callable, Iterator, List, Optional, Type, Union
import jwt
import requests
import tortilla
from tortilla.cache import BaseCache, DictCache
from tortilla.utils import Bunch, bunchify
from .paginator import PaginatedResults
from .utils import taglist_to_dict


class API:
    ENDPOINT = 'https://api.doujinshi.info/v1/'
    def __init__(self, refresh_deadline_sec=30, 
        tortilla_debug=False, tortilla_cache: Type[BaseCache]=DictCache(),
        tortilla_cache_lifetime: Optional[int]=None) -> None:
        self._api = tortilla.wrap(self.ENDPOINT, cache=tortilla_cache, cache_lifetime=tortilla_cache_lifetime, debug=tortilla_debug)
        self.refresh_deadline_sec = refresh_deadline_sec

    ### Auth
    def set_access_token(self, access_token: str) -> None:
        self.access_token = access_token
        self._api.config['headers']['Authorization'] = 'Bearer {}'.format(access_token) 
        self.me = bunchify(jwt.decode(access_token, verify=False))
        self.expires_at = datetime.fromtimestamp(self.me.exp)

    def register(self, name: str, email: str, password: str, password_confirmation: str) -> None:
        res: Bunch = self._api.auth.create.post(params={
            'name': name, 'email': email, 'password': password, 'password_confirmation': password_confirmation
        })
        self.set_access_token(res.access_token)
        self.refresh_token = res.refresh_token

    def login(self, email: str, password: str) -> None: 
        res: Bunch = self._api.auth.login.post(params={
            'email': email, 'password': password
        })
        self.set_access_token(res.access_token)
        self.refresh_token = res.refresh_token

    def do_refresh_token(self) -> None:
        # If the time remaining before the expiration time 
        # is less than a set number of seconds (default: 30 seconds), update the token.
        if self.expires_at - datetime.now() < timedelta(seconds=self.refresh_deadline_sec):
            res: Bunch = self._api.auth.login.post(params={
              'user': self.me['sub'], 'refresh_token': self.refresh_token
            }, cache_lifetime=None)
            self.set_access_token(res.access_token)
        else:
            pass
    
    ### Tags
    def get_tag_types(self) -> Bunch:
        return self._api.tag.types.get().data

    def get_all_tags(self, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.tag.get, params={'page': page, 'limit': limit})

    def get_all_tags_by_type(self, type: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.tag(type).get, params={'page': page, 'limit': limit})

    def get_tag(self, type: str, slug: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.tag(type)(slug).get, paginated_key='books', params={'page': page, 'limit': limit})

    def get_tag_changelog(self, type: str, slug: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.tag(type)(slug).changelog.get, params={'page': page, 'limit': limit})

    def create_tag(self, type: str, name_japanese: str, tags: List[str]=[], **kwargs: str) -> PaginatedResults:
        data = {'type': type, 'name_japanese': name_japanese}
        for key in ('name_romaji', 'name_english', 'aliases', 'description_english', 
        'description_japanese', 'date_start', 'date_end', 'links'):
            if key in kwargs:
                data[key] = kwargs[key]
        self.do_refresh_token()
        return PaginatedResults(self._api.tag.post, paginated_key='books', data=data)

    def update_tag(self, type: str, slug: str, name_japanese: str, tags: List[str]=[], **kwargs: str) -> PaginatedResults:
        data = {'name_japanese': name_japanese}
        for key in ('name_romaji', 'name_english', 'aliases', 'description_english', 
        'description_japanese', 'date_start', 'date_end', 'links'):
            if key in kwargs:
                data[key] = kwargs[key]
        self.do_refresh_token()
        return PaginatedResults(self._api.tag(type)(slug).put, paginated_key='books', data=data)

    ### doujinshi
    def get_all_doujinshi(self, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.book.get, params={'page': page, 'limit': limit})

    def get_doujinshi(self, slug: str) -> Bunch:
        return self._api.book(slug).get()

    def get_doujinshi_changelog(self, slug: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.book(slug).changelog.get, params={'page': page, 'limit': limit})

    def create_doujinshi(self, name_japanese: str, tag_ids: List[str]=[], **kwargs: Union[str, BinaryIO]) -> Bunch:
        params = {'name_japanese': name_japanese}
        params.update(taglist_to_dict(tag_ids))
        for key in ('name_romaji', 'name_english', 'date_released', 'pages', 'price', 
            'is_copybook', 'is_anthology', 'is_adult', 'is_novel', 'links'):
            if key in kwargs:
                params[key] = kwargs[key]
        files = {}
        for key in ('cover',): # 'samples')
            if key in kwargs:
                files[key] = kwargs[key]
        self.do_refresh_token()
        return self._api.book.post(params=params, files=files)

    def update_doujinshi(self, slug: str, name_japanese: str, tag_ids: List[str]=[], **kwargs: Union[str, BinaryIO]) -> Bunch:
        params = {'name_japanese': name_japanese}
        # Warning, this compretely REPLACES old tag list, 
        # so if you want simply add or remove tags, use methods below
        params.update(taglist_to_dict(tag_ids))
        for key in ('name_romaji', 'name_english', 'date_released', 'pages', 'price', 
            'is_copybook', 'is_anthology', 'is_adult', 'is_novel', 'links'):
            if key in kwargs:
                params[key] = kwargs[key]
        files = {}
        for key in ('cover',): # 'samples')
            if key in kwargs:
                files[key] = kwargs[key]
        self.do_refresh_token()
        return self._api.book(slug).post(params=params, files=files)

    def add_tags_to_doujinshi(self, slug: str, tag_ids: List[str]=[]) -> Bunch:
        # TODO WIP
        doujinshi = self.get_doujinshi(slug)
        new_ids = list(set([tag.id for tag in doujinshi.tags.data] + tag_ids))
        return self.update_doujinshi(slug, doujinshi.name.japanese, new_ids)

    def import_doujinshi(self, url: str) -> Bunch:
        self.do_refresh_token()
        return self._api('import').post(data={'url': url})

    ### Changelog
    def get_all_changelog(self, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.changelog.get, params={'page': page, 'limit': limit})

    def get_changelog(self, id: str) -> Bunch:
        return self._api.changelog(id).get()

    ### Search
    def search_doujinshi(self, query: str, page=1, limit=24, **kwargs: str) -> PaginatedResults:
        #TODO: boolean params actually takes 0 or 1
        params = {'q': query, 'page': page, 'limit': limit}
        for key in ('copybook', 'anthology', 'adult', 'novel'):
            if key in kwargs:
                params[key] = kwargs[key]
        return PaginatedResults(self._api.search.get, params=params)

    def search_tags(self, type: str, query: str, page=1, limit=24) -> PaginatedResults:
        params = {'q': query, 'page': page, 'limit': limit}
        return PaginatedResults(self._api.search.tag(type).get, params=params)

    def image_search(self, image, page=1, limit=24):
        files = {'image': image}
        params = {'page': page, 'limit': limit}
        self.do_refresh_token()
        return PaginatedResults(self._api.search.image.post, files=files, params=params)

    ### Users
    def get_user(self, slug: str) -> Bunch:
        return self._api.user(slug).get()

    def get_users_contributions(self, slug: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.user(slug).contributions.get, params={'page': page, 'limit': limit})

    #def update_settings(self):
    #    pass

    ### User Libraries
    def get_users_library(self, slug: str, type: str, page=1, limit=24) -> PaginatedResults:
        return PaginatedResults(self._api.user(slug).library(type).get, params={'page': page, 'limit': limit})

    def check_library_entry(self, type: str, book_id: str) -> bool:
        self.do_refresh_token()
        return self._api.library(type)(book_id).get().data

    def add_library_entry(self, type: str, book_id: str) -> None:
        self.do_refresh_token()
        self._api.library(type).post(data={'book': book_id})

    def remove_library_entry(self, type: str, book_id: str) -> None:
        self.do_refresh_token()
        self._api.library(type).delete(data={'book': book_id})

    ### Followed Tags
    def get_users_following_tags(self, slug: str, page=1, limit=24) -> PaginatedResults:
        self.do_refresh_token()
        return PaginatedResults(self._api.user(slug).following.get, params={'page': page, 'limit': limit})

    def check_following_tag(self, tag_id: str) -> bool:
        self.do_refresh_token()
        return self._api.following(tag_id).get().data

    def follow_tag(self, tag_id: str) -> None:
        self.do_refresh_token()
        self._api.following.post(data={'tag': tag_id})

    def unfollow_tag(self, tag_id: str) -> None:
        self.do_refresh_token()
        self._api.following.delete(data={'tag': tag_id})

    ### Notifications
    def get_notifications(self, page=1, limit=24) -> PaginatedResults:
        self.do_refresh_token()
        return PaginatedResults(self._api.notifications.get, params={'page': page, 'limit': limit})

    def get_unread_notifications_count(self) -> int:
        self.do_refresh_token()
        return self._api.notifications.count.get().data

    def mark_notification_as_read(self, notification_id: str) -> Bunch:
        self.do_refresh_token()
        return self._api.notifications.read.put(data={'notification': notification_id}).data

    def mark_all_notifications_as_read(self) -> Bunch:
        self.do_refresh_token()
        return self._api.notifications.read.all.put().data
