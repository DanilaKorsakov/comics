import os
import random

import requests
from urllib.parse import urlparse
from dotenv import load_dotenv


def get_comic_info(comic_id):

    url = f'https://xkcd.com/{comic_id}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()

    response_json = response.json()
    
    image_url = response_json['img']
    comment = response_json['alt']
    name = response_json['title']

    return image_url, comment, name
  

def get_extension(url):
    path = urlparse(url).path
    return os.path.splitext(path)[1]


def save_image(name, url):

    filename = f'{name}{get_extension(url)}'
    
    response = requests.get(url)
    response.raise_for_status()

    with open(filename, 'wb') as file:
        file.write(response.content)
    return filename


def get_upload_url(group_id, token, version):

    params = {
      'group_id': group_id,
      'access_token': token,
      'v': version
    }
  
    url='https://api.vk.com/method/photos.getWallUploadServer'
    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()['response']['upload_url']


def upload_image_to_server(token, group_id, version, filename):

    url = get_upload_url(group_id,token,version)

    with open(filename, 'rb') as file:
      
        files = {
            'photo': file
        }

        response = requests.post(url, files=files)
        response.raise_for_status()

    response_json = response.json()
    server = response_json['server']
    response_hash = response_json['hash']
    photo = response_json['photo']

    return server, response_hash, photo


def upload_comic_to_wall(token, group_id, version, filename):

    server, response_hash, photo = upload_image_to_server(token,group_id,version,filename)

    url = 'https://api.vk.com/method/photos.saveWallPhoto'

    params = {
        'access_token': token,
        'photo': photo,
        'v': version,
        'group_id': group_id,
        'server': server,
        'hash': response_hash
    }

    response = requests.post(url, params=params)
    response.raise_for_status()

    owner_id = response.json()['response'][0]['owner_id']
    media_id = response.json()['response'][0]['id']

    return owner_id, media_id


def publish_comic_to_group(token, group_id, version, filename, comment):

    url = 'https://api.vk.com/method/wall.post'

    owner_id, media_id = upload_comic_to_wall(token, group_id, version, filename)

    attachments = f'photo{owner_id}_{media_id}'

    params = {
      'access_token': token,
      'v': version,
      'attachments': attachments,
      'owner_id': -group_id,
      'message': comment,
      'from_group': '1'
    }
  
    response = requests.post(url, params=params)
    response.raise_for_status()


def get_last_comic_num():
  
    last_comic_url = "https://xkcd.com/info.0.json"
    response = requests.get(last_comic_url)
    response.raise_for_status()
  
    return response.json()["num"]


def generate_random_comic():

    last_comic_num = get_last_comic_num()

    random_comic_num = random.randint(1, last_comic_num)

    return random_comic_num


def main():

    load_dotenv()

    version = 5.131
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = int(os.getenv('VK_GROUP_ID'))
    try:
        comic_num = generate_random_comic()
        image_url, comment, title = get_comic_info(comic_num)
        filename = save_image(title, image_url)
    
        publish_comic_to_group(vk_access_token, group_id, version, filename, comment)
    finally:
        os.remove(filename)


if __name__ == "__main__":
    main()