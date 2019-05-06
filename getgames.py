import requests
from bs4 import BeautifulSoup
import json
import os
import urllib3
from fire import Fire
import logging
from path import Path
import enlighten
from slugify import slugify

logger = logging.getLogger('3djuegos')
logging.basicConfig(level=logging.DEBUG)

logger.info('This is running SYNC and WITHOUT POOL')

base_number = 0
base_url = 'https://www.3djuegos.com/novedades/juegos-generos/juegos/{}pf0f0f0/juegos-populares/'


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

def get_game_data(url):

    logger.debug(f'Download game info from: {url}')
    r = requests.get(url)

    assert r.status_code == 200, "The request was not sucesfull"

    soup = BeautifulSoup(r.text, 'html.parser')

    description = soup.select_one('#adpepito').text

    data = soup.findAll('script', attrs={'type': 'application/ld+json'})[2]

    data = json.loads(data.text)
    data['description'] = description
    data['safe-name'] = slugify(data['name'])
    data['url'] = url


    return data


def get_thumbail(data):
    logger.debug(
        f'Download thumbail of {data["name"]} from: {data["thumbnailUrl"]}')

    thumbnail = requests.get(data['thumbnailUrl'])
    (thumbails_dir/data['safe-name'] + '.jpg').write_bytes(thumbnail.content)


def get_image(data):
    logger.debug(f'Download image of {data["name"]} from: {data["image"]}')

    thumbnail = requests.get(data['image'])
    (images_dir/data['safe-name'] + '.jpg').write_bytes(thumbnail.content)


def get_games_list(url):
    logger.debug(f'Download game list from: {url}')

    r = requests.get(url)

    assert r.status_code == 200, "The request was not sucesfull"

    soup = BeautifulSoup(r.text, 'html.parser')

    articles = soup.select('article')

    return [a.a.attrs['href'] for a in articles]


def get_game(url):

    if url in saved_games and not Config.overwrite:
        return

    data = get_game_data(url)

    json.dump(data, (base_path/data['safe-name'] + '.json').open('w'),
              ensure_ascii=False, indent=2)

    if Config.thumbnail:
        get_thumbail(data)

    if Config.image:
        get_image(data)


def get_all_games(begining=0, end=611):
    logger.debug(f'From {begining} to {end}')
    manager = enlighten.get_manager()

    pages = manager.counter(total=end-begining, desc='Page:', unit='pages')

    for i in range(begining, end):

        game_list = get_games_list(base_url.format(i))

        games = manager.counter(total=len(game_list),
                                desc='  Game:', unit='games', leave=False)

        for url in get_games_list(base_url.format(i)):

            get_game(url)

            # except Exception as e:
            #     logger.error(e)

            games.update()
        games.close()
        pages.update()

    manager.stop()  # Clears all temporary counters and progress bars


if __name__ == "__main__":
    Fire()
    # get_all_games()
