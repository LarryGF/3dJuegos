import os
import json
import dbm
import asyncio
import logging
import requests_async as requests
from bs4 import BeautifulSoup
from path import Path
import enlighten
from slugify import slugify
import asyncio
import aiofiles
PARSER = 'lxml'
try:
    import lxml
except ImportError:
    PARSER = 'html.parser'

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

LOCK = asyncio.Lock()

if os.path.exists(os.path.join(MODULE, 'config.json')):
    CONFIG = json.load(open(os.path.join(MODULE, 'config.json')))
else:
    CONFIG = {
        "base_url": "https://www.3djuegos.com/novedades/juegos-generos/juegos/{}pf0f0f0/juegos-populares/",
        "thumbnail": False,
        "image": False,
        "overwrite": False,
        "base_path": "games",
        "database": "games.db",
        "begining": 0,
        "end": 611
    }
    json.dump(CONFIG, open(os.path.join(MODULE, 'config.json'), 'w'), indent=2)

logger = logging.getLogger('3djuegos')
# logging.basicConfig(level=logging.DEBUG)

logger.info('This is running SYNC and WITHOUT POOL')


class Config():
    thumbnail = CONFIG['thumbnail']
    image = CONFIG['image']
    overwrite = CONFIG['overwrite']


class Database:

    def __init__(self):
        self._path = os.path.join(
            os.getcwd(), CONFIG['base_path'], CONFIG['database'])
        with dbm.open(self._path, 'c') as data:
            pass

    def __contains__(self, key: str):
        with dbm.open(self._path) as data:
            inn = key in data
        return inn

    def __getitem__(self, key: str):
        with dbm.open(self._path) as data:
            value = data[key]
        return value

    def __setitem__(self, key: str, value: str):
        with dbm.open(self._path) as data:
            data[key] = value

    def __delitem__(self, key: str):
        with dbm.open(self._path) as data:
            del data[key]


class Scrapper:
    def __init__(self, base_url: str = CONFIG['base_url'], begining: int = CONFIG['begining'], end: int = CONFIG['end']):
        self.base_url = base_url
        self.begining = begining
        self.end = end
        self.base_path = Path(os.path.join(os.getcwd(), CONFIG['base_path']))
        self.base_path.mkdir_p()
        self.games_dir = self.base_path / 'games'
        self.games_dir.mkdir_p()
        self.images_dir = self.base_path / 'images'
        self.images_dir.mkdir_p()
        self.thumbails_dir = self.base_path / 'thumbails'
        self.thumbails_dir.mkdir_p()
        self.manager = enlighten.get_manager()
        self.database = Database()

    @staticmethod
    async def get_game_data(url):

        logger.debug(f'Download game info from: {url}')
        r = await requests.get(url)

        assert r.status_code == 200, "The request was not sucesfull"

        soup = BeautifulSoup(r.text, PARSER)

        description = soup.select_one('#adpepito').text

        platforms = [i.text for i in soup.select_one('dd').findChildren()]

        data = soup.findAll('script', attrs={'type': 'application/ld+json'})[2]

        data = json.loads(data.text)
        platforms.insert(0, data['gamePlatform'])
        data['description'] = description
        data['name'] = str(data['name'])
        data['safe-name'] = slugify(data['name']) + \
            '-[' + data['gamePlatform']+']'
        data['url'] = url
        data['platforms'] = platforms

        return data

    async def get_thumbail(self, data):
        logger.debug(
            f'Download thumbail of {data["name"]} from: {data["thumbnailUrl"]}')

        thumbnail = await requests.get(data['thumbnailUrl'])

        async with aiofiles.open((self.thumbails_dir/data['safe-name'] + '.jpg').abspath(), 'wb') as outfile:
            await outfile.write(thumbnail.content)

    async def get_image(self, data):
        logger.debug(f'Download image of {data["name"]} from: {data["image"]}')

        thumbnail = await requests.get(data['image'])

        async with aiofiles.open((self.images_dir/data['safe-name'] + '.jpg').abspath(), 'wb') as outfile:
            await outfile.write(thumbnail.content)

    @staticmethod
    async def get_games_list(url):
        logger.debug(f'Download game list from: {url}')

        r = await requests.get(url)

        assert r.status_code == 200, "The request was not sucesfull"

        soup = BeautifulSoup(r.text, PARSER)

        articles = soup.select('article')

        return [a.a.attrs['href'] for a in articles]

    @staticmethod
    def dict_of_elements(elements):

        ans = {}

        for line in elements:
            if ':' in line:
                split = line.split(':')
                left = split[0]
                right = ':'.join(split[1:])
                ans[left.strip()] = right.strip()

        return ans

    @staticmethod
    async def requiremts_extract(url):
        r = await requests.get(url)

        soup = BeautifulSoup(r.text, PARSER)
        foro = soup.select('.list_foro')
        if not foro:
            logger.debug(f'Not foro in: {url}')
            return {'min': {}, 'rec': {}}
        min, recomend = foro

        min = list(map(lambda x: x.text, min.select('li')))
        recomend = list(map(lambda x: x.text, recomend.select('li')))

        min_clean = {'min': Scrapper.dict_of_elements(
            min), 'rec': Scrapper.dict_of_elements(recomend)}

        return min_clean

    async def get_game(self, url, game_bar=None):
        ret = False
        async with LOCK:
            if url in self.database and not Config.overwrite:
                ret = True
        if ret:
            return

        data = await Scrapper.get_game_data(url)

        if data['gamePlatform'] == 'PC':

            req_url = ''
            if 'juegos' == url.split('/')[3]:
                req_url = url[:32] + 'requisitos/' + url[35:]

            else:
                req_url = url[:25] + 'juegos/requisitos/' + url[25:]

            req = await Scrapper.requiremts_extract(req_url)
            data['PCrequirements'] = req

            # except Exception as e:
            #     logger.error(str(e))
            #     logger.error(f'Fail url: {req_url}\nFrom: {url}')

        futures = []

        async with aiofiles.open((self.games_dir/data['safe-name'] + '.json').abspath(), 'w') as outfile:
            await outfile.write(json.dumps(data,
                                           ensure_ascii=False, indent=2))

        if Config.thumbnail:
            futures.append(get_thumbail(data))

        if Config.image:
            futures.append(get_image(data))

        if futures:
            await asyncio.wait(futures)

        if game_bar is not None:
            game_bar.update()

    async def get_page(self, url, page_bar=None):

        game_list = await Scrapper.get_games_list(url)

        games_bar = self.manager.counter(total=len(game_list),
                                         desc='  Game:', unit='games', leave=False)

        await asyncio.wait([self.get_game(game, games_bar) for game in game_list])
        games_bar.close()

        if page_bar is not None:
            page_bar.update()

    async def get_all_games(self):
        base_url = self.base_url
        begining = self.begining
        end = self.end
        logger.debug(f'From {begining} to {end}')

        pages = self.manager.counter(
            total=end-begining, desc='Page:', unit='pages')

        dltasks = set()

        for i in range(begining, end):

            if len(dltasks) > 5:
                _done, dltasks = await asyncio.wait(
                    dltasks, return_when=asyncio.FIRST_COMPLETED)

            dltasks.add(self.get_page(base_url.format(i), pages))

        # page_future = [get_page(base_url.format(i), pages) for i in range(begining, end)]

        await asyncio.wait(dltasks)
        self.manager.stop()  # Clears all temporary counters and progress bars
