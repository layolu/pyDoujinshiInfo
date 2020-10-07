from abc import ABCMeta, abstractmethod
from tortilla.utils import Bunch, bunchify


class Item(Bunch, metaclass=ABCMeta):
    @abstractmethod
    @property
    def page_urls(self):
        pass


class TagItem(Item):
    URL_BASE = 'https://{}doujinshi.info/tag/{}/{}'

    @property
    def page_urls(self):
        return TagItem.URL_BASE.format('', self.type.slug, self.slug)


class BookItem(Item):
    URL_BASE = 'https://{}doujinshi.info/book/{}'

    @property
    def page_urls(self):
        return BookItem.URL_BASE.format('', self.slug)
