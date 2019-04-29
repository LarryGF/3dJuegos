import requests
from bs4 import BeautifulSoup
import json
from fire import Fire

base_url = 'https://www.3djuegos.com/novedades/juegos-generos/juegos/{}pf0f0f0/juegos-populares/'


def get_game(url):
    r = requests.get(url)

    assert r.status_code == 200, "The request was not sucesfull"

    soup = BeautifulSoup(r.text, 'html.parser')

    description = soup.select_one('#adpepito').text

    data = soup.findAll('script', attrs={'type': 'application/ld+json'})[2]

    data = json.loads(data.text)
    data['description'] = description

    return data


def get_games_list(url):
    r = requests.get(url)

    assert r.status_code == 200, "The request was not sucesfull"

    soup = BeautifulSoup(r.text, 'html.parser')

    articles = soup.select('article')

    return [a.a.attrs['href'] for a in articles]


def get_all_games():

    ans = []
    for i in range(112):
        ans.extend([get_game(url)
                    for url in get_games_list(base_url.format(i))])

    return ans


if __name__ == "__main__":
    Fire()
