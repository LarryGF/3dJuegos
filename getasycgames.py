import requests_async as requests
from bs4 import BeautifulSoup
import json
import os
import logging
from path import Path
import enlighten
from slugify import slugify
import asyncio
import aiofiles

logger = logging.getLogger('3djuegos')
# logging.basicConfig(level=logging.DEBUG)

logger.info('This is running SYNC and WITHOUT POOL')

base_number = 0
base_url = 'https://www.3djuegos.com/novedades/juegos-generos/juegos/{}pf0f0f0/juegos-populares/'
base_url = 'https://www.3djuegos.com/novedades/juegos-generos/juegos-pc/{}f1f0f0/juegos-populares/'

class Config():
    thumbnail = False
    image = False
    overwrite = False


saved_games = []

if not os.path.exists('games'):
    os.makedirs('games')

base_path = Path('games')

games_dir = os.path.join(os.getcwd(), 'games')

images_dir = base_path / 'images'
images_dir.mkdir_p()

thumbails_dir = base_path / 'thumbails'
thumbails_dir.mkdir_p()

manager = enlighten.get_manager()


async def get_game_data(url):

    logger.debug(f'Download game info from: {url}')
    r = await requests.get(url)

    assert r.status_code == 200, "The request was not sucesfull"

    soup = BeautifulSoup(r.text, 'html.parser')

    description = soup.select_one('#adpepito').text

    data = soup.findAll('script', attrs={'type': 'application/ld+json'})[2]

    data = json.loads(data.text)
    data['description'] = description
    data['name'] = str(data['name'])
    data['safe-name'] = slugify(data['name']) + '-[' + data['gamePlatform']+']'
    data['url'] = url

    return data


async def get_thumbail(data):
    logger.debug(
        f'Download thumbail of {data["name"]} from: {data["thumbnailUrl"]}')

    thumbnail = await requests.get(data['thumbnailUrl'])

    async with aiofiles.open((thumbails_dir/data['safe-name'] + '.jpg').abspath(), 'wb') as outfile:
        await outfile.write(thumbnail.content)


async def get_image(data):
    logger.debug(f'Download image of {data["name"]} from: {data["image"]}')

    thumbnail = await requests.get(data['image'])

    async with aiofiles.open((images_dir/data['safe-name'] + '.jpg').abspath(), 'wb') as outfile:
        await outfile.write(thumbnail.content)


async def get_games_list(url):
    logger.debug(f'Download game list from: {url}')

    r = await requests.get(url)

    assert r.status_code == 200, "The request was not sucesfull"

    soup = BeautifulSoup(r.text, 'html.parser')

    articles = soup.select('article')

    return [a.a.attrs['href'] for a in articles]


def dict_of_elements(elements):


    ans = {}

    for line in elements:
        if ':' in line:
            split = line.split(':')
            left = split[0]
            right = ':'.join(split[1:])
            ans[left.strip()] = right.strip()

    return ans

async def requiremts_extract(url):
    r = await requests.get(url)

    soup = BeautifulSoup(r.text, 'html.parser')
    foro = soup.select('.list_foro')
    if not foro:
        logger.debug(f'Not foro in: {url}')
        return {'min':{}, 'rec':{}}
    min, recomend = foro

    min = list(map(lambda x: x.text, min.select('li')))
    recomend = list(map(lambda x: x.text, recomend.select('li')))

    min_clean = {'min': dict_of_elements(min), 'rec': dict_of_elements(recomend)}

    return min_clean


async def get_game(url, game_bar=None):

    if url in saved_games and not Config.overwrite:
        return

    data = await get_game_data(url)

    if data['gamePlatform'] == 'PC':

        req_url = ''
        if 'juegos' == url.split('/')[3]:
            req_url = url[:32]  + 'requisitos/' + url[35:]

        else:
            req_url = url[:25] + 'juegos/requisitos/' + url[25:]

        req = await requiremts_extract(req_url)
        data['PCrequirements'] = req

        # except Exception as e:
        #     logger.error(str(e))
        #     logger.error(f'Fail url: {req_url}\nFrom: {url}')

    futures = []

    async with aiofiles.open((base_path/data['safe-name'] + '.json').abspath(), 'w') as outfile:
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


async def get_page(url, page_bar=None):

    game_list = await get_games_list(url)

    games_bar = manager.counter(total=len(game_list),
                                desc='  Game:', unit='games', leave=False)

    await asyncio.wait([get_game(game, games_bar) for game in game_list])
    games_bar.close()

    if page_bar is not None:
        page_bar.update()


async def arange(*args, **kargs):
    return range(*args, **kargs)


async def get_all_games(base_url=base_url, begining=0, end=611):
    logger.debug(f'From {begining} to {end}')

    pages = manager.counter(total=end-begining, desc='Page:', unit='pages')

    dltasks = set()

    for i in range(begining, end):

        if len(dltasks) > 5:
            _done, dltasks = await asyncio.wait(
                dltasks, return_when=asyncio.FIRST_COMPLETED)

        dltasks.add(get_page(base_url.format(i), pages))

    # page_future = [get_page(base_url.format(i), pages) for i in range(begining, end)]

    await asyncio.wait(dltasks)
    manager.stop()  # Clears all temporary counters and progress bars



Config.thumbnail = False
Config.image = False
Config.overwrite = False

if __name__ == "__main__":
    # get_all_games()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(get_all_games(base_url, 0, 100))
