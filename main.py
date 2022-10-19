import os
import random

import requests
from urllib.parse import urlparse
from dotenv import load_dotenv


def get_comics_info(comics_id):

    url = f'https://xkcd.com/{comics_id}/info.0.json'
    response = requests.get(url)
    response.raise_for_status()

    answer = response.json()
    
    image_url = answer['img']
    comment = answer['alt']
    name = answer['title']

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


def upload_to_server(token, group_id, version, filename):

    url = get_upload_url(group_id,token,version)

    with open(filename, 'rb') as file:
      
        files = {
            'photo': file
        }

        response = requests.post(url, files=files)
        response.raise_for_status()

    answer = response.json()
    server = answer['server']
    response_hash = answer['hash']
    photo = answer['photo']

    return server, response_hash, photo


def upload_comics_to_wall(token, group_id, version, filename):

    server, response_hash, photo = upload_to_server(token,group_id,version,filename)

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

    return response.json()['response']


def publish_comics_to_group(token, group_id, version, filename, comment):

    url = 'https://api.vk.com/method/wall.post'

    saved_image_info = upload_comics_to_wall(token, group_id, version, filename)

    owner_id = saved_image_info[0]['owner_id']
    media_id = saved_image_info[0]['id']

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

    os.remove(filename)


def get_last_comics_num():
  
    last_comics_url = "https://xkcd.com/info.0.json"
    response = requests.get(last_comics_url)
    response.raise_for_status()
  
    return response.json()["num"]


def generate_random_comics():

    last_comics_num = get_last_comics_num()

    random_comics_num = random.randint(1, last_comics_num)

    return random_comics_num


def main():

    load_dotenv()

    version = 5.131
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = int(os.getenv('VK_GROUP_ID'))
    comics_num = generate_random_comics()
    image_url, comment, title = get_comics_info(comics_num)
    filename = save_image(title, image_url)
    
    publish_comics_to_group(vk_access_token, group_id, version, filename, comment)


if __name__ == "__main__":
    main()