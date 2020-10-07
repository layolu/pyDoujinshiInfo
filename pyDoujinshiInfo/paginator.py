from typing import Any, BinaryIO, Callable, Dict, Iterator, Union
import requests
from tortilla.utils import Bunch, bunchify


class PaginatedResults:
    def __init__(self, req: Callable[..., Bunch],
                 paginated_key: str = None, params={},
                 **kwargs: Union[Dict[str, str], Dict[str, int], Dict[str, BinaryIO]]) -> None:
        self._req = req
        self.params = params
        self.req_options = {}
        for key in ('data', 'files'):
            if key in kwargs:
                self.req_options[key] = kwargs[key]
        self.paginated_key = paginated_key
        try:
            # self.res = getattr(self._wrap, self.method)(params=self.params, **self.req_options)
            self.res = self._req(params=self.params, **self.req_options)
            self.first_res = bunchify(self.res.copy())
            self.total_num = self._get_page(self.first_res).meta.total
        except requests.exceptions.HTTPError:
            raise
        if self.paginated_key:
            # return data except paginated values
            # TODO: considering making the entire contents of the dictionary members of the object
            self.data = bunchify({k: v for k, v in self.res.items() if k != self.paginated_key})
        else:
            self.data = Bunch()

    def __str__(self) -> str:
        # TODO: id or slug, that is the question.
        if self.data.id:
            return self.data.id
        else:
            return ''

    def __call__(self, key=None) -> Union[Bunch, Any]:
        if key:
            return self.data[key]
        else:
            return self.data

    def _get_page(self, res: Bunch) -> Bunch:
        page: Bunch
        if self.paginated_key:
            page = res[self.paginated_key]
        else:
            page = res
        return page

    def results(self, limit=24) -> Iterator[Bunch]:
        page: Bunch
        page = self._get_page(self.first_res)
        if page.data:
            yield from page.data[0:limit]
            limit -= len(page.data)
            if limit <= 0:
                return
        while page.meta.current_page < page.meta.last_page:
            # TODO: Maybe I should use a vanilla requests after the 1st request
            self.params.update({'page': page.meta.current_page + 1,
                                'limit': page.meta.per_page})
            try:
                # self.res = getattr(self._wrap, self.method)(
                self.res = self._req(params=self.params, **self.req_options)
            except requests.exceptions.HTTPError:
                raise
            page = self._get_page(self.res)
            yield from page.data[0:limit]
            limit -= len(page.data)
            if limit <= 0:
                return
