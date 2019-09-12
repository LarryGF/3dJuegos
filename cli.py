import os
import json
import fire
import asyncio
from game_scraper import Scrapper

try:
    MODULE = os.path.dirname(os.path.realpath(__file__))
except:
    MODULE = ""

BASE_CONFIG = {
        "base_url" : "https://www.3djuegos.com/novedades/juegos-generos/juegos/{}pf0f0f0/juegos-populares/",
        "thumbnail": False,
        "image": False,
        "overwrite": False,
        "base_path": "games",
        "database": "games.db",
        "begining": 0,
        "end": 611
    }


class CLI:

    def get_all_games(self, begining=None, end=None):
        args = {i:j for i,j in zip(['begining','end'],[begining,end]) if j}
        sc = Scrapper(**args)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(sc.get_all_games())

    def config(self):
        if os.path.exists(os.path.join(MODULE, 'config.json')):
            CONFIG = json.load(open(os.path.join(MODULE, 'config.json')))
        else:
            CONFIG = BASE_CONFIG
        return CONFIG


    def set_beginin(self, n: int):
        assert isinstance(n, int) and n>=0
        if os.path.exists(os.path.join(MODULE, 'config.json')):
            CONFIG = json.load(open(os.path.join(MODULE, 'config.json')))
        else:
            CONFIG = BASE_CONFIG
        CONFIG['begining'] = n
        json.dump(CONFIG, open(os.path.join(MODULE, 'config.json'), 'w'), indent=2)

    def set_end(self, n: int):
        assert isinstance(n, int) and n>=0
        if os.path.exists(os.path.join(MODULE, 'config.json')):
            CONFIG = json.load(open(os.path.join(MODULE, 'config.json')))
        else:
            CONFIG = BASE_CONFIG
        CONFIG['end'] = n
        json.dump(CONFIG, open(os.path.join(MODULE, 'config.json'), 'w'), indent=2)

    def thumbnail(self, val: bool):
        assert isinstance(val, bool) or isinstance(val, int)
        if os.path.exists(os.path.join(MODULE, 'config.json')):
            CONFIG = json.load(open(os.path.join(MODULE, 'config.json')))
        else:
            CONFIG = BASE_CONFIG
        CONFIG['thumbnail'] = bool(val)
        json.dump(CONFIG, open(os.path.join(MODULE, 'config.json'), 'w'), indent=2)

    def image(self, val: bool):
        assert isinstance(val, bool) or isinstance(val, int)
        if os.path.exists(os.path.join(MODULE, 'config.json')):
            CONFIG = json.load(open(os.path.join(MODULE, 'config.json')))
        else:
            CONFIG = BASE_CONFIG
        CONFIG['image'] = bool(val)
        json.dump(CONFIG, open(os.path.join(MODULE, 'config.json'), 'w'), indent=2)

    def overwrite(self, val: bool):
        assert isinstance(val, bool) or isinstance(val, int)
        if os.path.exists(os.path.join(MODULE, 'config.json')):
            CONFIG = json.load(open(os.path.join(MODULE, 'config.json')))
        else:
            CONFIG = BASE_CONFIG
        CONFIG['overwrite'] = bool(val)
        json.dump(CONFIG, open(os.path.join(MODULE, 'config.json'), 'w'), indent=2)

if __name__ == "__main__":
    fire.Fire(CLI)