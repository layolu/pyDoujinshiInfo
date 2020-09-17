from datetime import datetime, timedelta
import jwt
import requests
import tortilla


class API:
    ENDPOINT = 'https://api.doujinshi.info/v1/'
    def __init__(self, refresh_deadline_sec=30, 
        tortilla_debug=False, tortilla_cache=tortilla.cache.DictCache(), tortilla_cache_lifetime=None):
        self._api = tortilla.wrap(self.ENDPOINT, cache=tortilla_cache, cache_lifetime=tortilla_cache_lifetime, debug=tortilla_debug)
        self.refresh_deadline_sec = refresh_deadline_sec

    ### Auth
    def set_access_token(self, access_token: str):
        self.access_token = access_token
        self._api.config['headers']['Authorization'] = 'Bearer {}'.format(access_token) 
        self.me = tortilla.utils.bunchify(jwt.decode(access_token, verify=False))
        self.expires_at = datetime.fromtimestamp(self.me.exp)

    def register(self, name: str, email: str, password: str, password_confirmation: str):
        res = self._api.auth.create.post(params={
            'name': name, 'email': email, 'password': password, 'password_confirmation': password_confirmation
        })
        self.set_access_token(res.access_token)
        self.refresh_token = res.refresh_token

    def login(self, email: str, password: str): 
        res = self._api.auth.login.post(params={
            'email': email, 'password': password
        })
        self.set_access_token(res.access_token)
        self.refresh_token = res.refresh_token

    def do_refresh_token(self):
        # If the time remaining before the expiration time 
        # is less than a set number of seconds (default: 30 seconds), update the token.
        if self.expires_at - datetime.now() < timedelta(seconds=self.refresh_deadline_sec):
            res = self._api.auth.login.post(params={
              'user': self.me['sub'], 'refresh_token': self.refresh_token
            }, cache_lifetime=None)
            self.set_access_token(res.access_token)
        else:
            pass
    
    ### Tags
    def get_tag_types(self):
        return self._api.tag.types.get().data

    def get_all_tags(self, page=1, limit=24):
        return PaginatedResults(self._api.tag, params={'page': page, 'limit': limit})

    def get_all_tags_by_type(self, type: str, page=1, limit=24):
        return PaginatedResults(self._api.tag(type), params={'page': page, 'limit': limit})

    def get_tag(self, type: str, slug: str, page=1, limit=24):
        return PaginatedResults(self._api.tag(type)(slug), paginated_key='books', params={'page': page, 'limit': limit})

    def get_tag_changelog(self, type: str, slug: str, page=1, limit=24):
        return PaginatedResults(self._api.tag(type)(slug).changelog, params={'page': page, 'limit': limit})

    def create_tag(self, type: str, name_japanese: str, **kwargs):
        data = {'type': type, 'name_japanese': name_japanese}
        for key in ('name_romaji', 'name_english', 'aliases', 'description_english', 
        'description_japanese', 'date_start', 'date_end', 'tags', 'links'):
            if key in kwargs:
                data[key] = kwargs[key]
        self.do_refresh_token()
        return PaginatedResults(self._api.tag, method='post', paginated_key='books', data=data)

    def update_tag(self, type: str, slug: str, name_japanese: str, **kwargs):
        data = {'name_japanese': name_japanese}
        for key in ('name_romaji', 'name_english', 'aliases', 'description_english', 
        'description_japanese', 'date_start', 'date_end', 'tags', 'links'):
            if key in kwargs:
                data[key] = kwargs[key]
        self.do_refresh_token()
        return PaginatedResults(self._api.tag(type)(slug), method='put', paginated_key='books', data=data)

    ### doujinshi
    def get_all_doujinshi(self, page=1, limit=24):
        return PaginatedResults(self._api.book, params={'page': page, 'limit': limit})

    def get_doujinshi(self, slug: str):
        return self._api.book(slug).get()

    def get_doujinshi_changelog(self, slug: str, page=1, limit=24):
        return PaginatedResults(self._api.book(slug).changelog, params={'page': page, 'limit': limit})

    def create_doujinshi(self, name_japanese: str, **kwargs):
        params = {'name_japanese': name_japanese}
        for key in ('name_romaji', 'name_english', 'date_released', 'pages', 'price', 
            'is_copybook', 'is_anthology', 'is_adult', 'is_novel', 'tags', 'links'):
            if key in kwargs:
                params[key] = kwargs[key]
        files = {}
        for key in ('cover',): # 'samples')
            if key in kwargs:
                files[key] = kwargs[key]
        self.do_refresh_token()
        return self._api.book.post(params=params, files=files)

    def update_doujinshi(self, slug: str, name_japanese: str, **kwargs):
        params = {'name_japanese': name_japanese}
        for key in ('name_romaji', 'name_english', 'date_released', 'pages', 'price', 
            'is_copybook', 'is_anthology', 'is_adult', 'is_novel', 'tags', 'links'):
            if key in kwargs:
                params[key] = kwargs[key]
        files = {}
        for key in ('cover',): # 'samples')
            if key in kwargs:
                files[key] = kwargs[key]
        self.do_refresh_token()
        return self._api.book(slug).post(params=params, files=files)

    def import_doujinshi(self, url: str):
        self.do_refresh_token()
        return self._api('import').post(data={'url': url})

    ### Changelog
    def get_all_changelog(self, page=1, limit=24):
        return PaginatedResults(self._api.changelog, params={'page': page, 'limit': limit})

    def get_changelog(self, id: str):
        return self._api.changelog(id).get()

    ### Search
    def search_doujinshi(self, query: str, page=1, limit=24, **kwargs):
        #TODO: boolean params actually takes 0 or 1
        params = {'q': query, 'page': page, 'limit': limit}
        for key in ('copybook', 'anthology', 'adult', 'novel'):
            if key in kwargs:
                params[key] = kwargs[key]
        return PaginatedResults(self._api.search, params=params)

    def search_tags(self, type: str, query: str, page=1, limit=24):
        params = {'q': query, 'page': page, 'limit': limit}
        return PaginatedResults(self._api.search.tag(type), params=params)

    def image_search(self, image, page=1, limit=24):
        files = {'image': image}
        params = {'page': page, 'limit': limit}
        self.do_refresh_token()
        return PaginatedResults(self._api.search.image, method='post', files=files, params=params)

    ### Users
    def get_user(self, slug: str):
        return self._api.user(slug).get()

    def get_users_contributions(self, slug: str, page=1, limit=24):
        return PaginatedResults(self._api.user(slug).contributions, params={'page': page, 'limit': limit})

    #def update_settings(self):
    #    pass

    ### User Libraries
    def get_users_library(self, slug: str, type: str, page=1, limit=24):
        return PaginatedResults(self._api.user(slug).library(type), params={'page': page, 'limit': limit})

    def check_library_entry(self, type: str, book_id: str):
        self.do_refresh_token()
        return self._api.library(type)(book_id).get().data

    def add_library_entry(self, type: str, book_id: str):
        self.do_refresh_token()
        self._api.library(type).post(data={'book': book_id})

    def remove_library_entry(self, type: str, book_id: str):
        self.do_refresh_token()
        self._api.library(type).delete(data={'book': book_id})

    ### Followed Tags
    def get_users_following_tags(self, slug: str, page=1, limit=24):
        self.do_refresh_token()
        return PaginatedResults(self._api.user(slug).following, params={'page': page, 'limit': limit})

    def check_following_tag(self, tag_id: str):
        self.do_refresh_token()
        return self._api.following(tag_id).get().data

    def follow_tag(self, tag_id: str):
        self.do_refresh_token()
        self._api.following.post(data={'tag': tag_id})

    def unfollow_tag(self, tag_id: str):
        self.do_refresh_token()
        self._api.following.delete(data={'tag': tag_id})

    ### Notifications
    def get_notifications(self, page=1, limit=24):
        self.do_refresh_token()
        return PaginatedResults(self._api.notifications, params={'page': page, 'limit': limit})

    def get_unread_notifications_count(self):
        self.do_refresh_token()
        return self._api.notifications.count.get().data

    def mark_notification_as_read(self, notification_id: str):
        self.do_refresh_token()
        return self._api.notifications.read.put(data={'notification': notification_id}).data

    def mark_all_notifications_as_read(self):
        self.do_refresh_token()
        return self._api.notifications.read.all.put().data


class PaginatedResults:
    def __init__(self, wrap: tortilla.wrappers.Wrap, paginated_key: str=None, method='get', params={}, **kwargs):
        self._wrap = wrap
        self.params = params
        self.req_options = {}
        for key in ('data', 'files'):
            if key in kwargs:
                self.req_options[key] = kwargs[key]
        self.method = method
        self.paginated_key = paginated_key
        try:
            #self.res = getattr(self._wrap, self.method)(params=self.params, **self.req_options)
            self.res = self._wrap.request(self.method, params=self.params, **self.req_options)
        except requests.exceptions.HTTPError:
            raise
        if self.paginated_key:
            # return data except paginated values
            # TODO: considering making the entire contents of the dictionary members of the object
            self.data = tortilla.utils.bunchify({k: v for k, v in self.res.items() if k != self.paginated_key})
        else:
            self.data = tortilla.utils.Bunch()
        self.first_res = tortilla.utils.bunchify(self.res.copy())
        self.total_num = self._get_page(self.first_res).meta.total

    def _get_page(self, res: tortilla.utils.Bunch):
        if self.paginated_key:
            page = res[self.paginated_key]
        else:
            page = res
        return page
        
    def results(self):
        page = self._get_page(self.first_res)
        if page.data:
            yield from page.data
        while page.meta.current_page < page.meta.last_page:
            # TODO: Maybe I should use a vanilla requests after the 1st request
            self.params.update({'page': page.meta.current_page + 1, 
                'limit': page.meta.per_page})
            try:
                #self.res = getattr(self._wrap, self.method)(
                self.res = self._wrap.request(self.method, params=self.params, **self.req_options)
            except requests.exceptions.HTTPError:
                raise
            page = self._get_page(self.res)
            yield from page.data
