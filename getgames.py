import requests
from bs4 import BeautifulSoup
import json
import os
import urllib3
from fire import Fire

base_url = 'https://www.3djuegos.com/novedades/juegos-generos/juegos/{}pf0f0f0/juegos-populares/'
if not os.path.exists('games'):
     os.makedirs('games')

games_dir = os.path.join(os.getcwd(), 'games')

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
    for i in range(612):
        for url in get_games_list(base_url.format(i)):
            game = get_game(url)
            game['name'] = game['name'].replace('/','-')
            print(game['name'])
            if not os.path.exists(os.path.join(games_dir, game['name'] + '.json')):
                print(game['name']+ ' saving json')
                json.dump(game, open(os.path.join(games_dir, game['name'] + '.json'), 'w'))
                thumbnail = requests.get(game['thumbnailUrl'])
                if not os.path.exists(os.path.join(games_dir, game['name'] + '_th.jpg')):
                    print(game['name']+ 'saving jpg')
                    file = open(os.path.join(games_dir, game['name'] + '_th.jpg'), 'wb')
                    file.write(thumbnail.content)
                    file.close()
        # ans.extend([get_game(url)
        #             for url in get_games_list(base_url.format(i))])
        # print(ans)

    
    # json.dump(ans, open('games.json', 'w'))

    # return ans


if __name__ == "__main__":
    Fire()
