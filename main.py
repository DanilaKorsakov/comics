import os
import random

import requests
from urllib.parse import urlparse
from dotenv import load_dotenv


def generate_random_comic():

    last_comic_url = "https://xkcd.com/info.0.json"
    response = requests.get(last_comic_url)
    response.raise_for_status()

    last_comic_num = response.json()["num"]

    random_comic_num = random.randint(1, last_comic_num)

    comic_url = f'https://xkcd.com/{random_comic_num}/info.0.json'
    response = requests.get(comic_url)
    response.raise_for_status()

    random_comic_response = response.json()

    image_url = random_comic_response['img']
    comment = random_comic_response['alt']
    name = random_comic_response['title']

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


def get_upload_url(token, version, group_id):

    params = {
        'access_token': token,
        'v': version,
        'group_id': group_id,
    }

    url = 'https://api.vk.com/method/photos.getWallUploadServer'
    response = requests.get(url, params=params)
    response.raise_for_status()
    check_response(response.json())

    return response.json()['response']['upload_url']


def upload_image_to_server(upload_url, filename):

    with open(filename, 'rb') as file:
      
        files = {
            'photo': file
        }

        response = requests.post(upload_url, files=files)

    response.raise_for_status()
    check_response(response.json())

    upload_response = response.json()
    server = upload_response['server']
    response_hash = upload_response['hash']
    photo = upload_response['photo']

    return server, response_hash, photo


def upload_comic_to_wall(token, version, group_id, server, response_hash, photo):

    url = 'https://api.vk.com/method/photos.saveWallPhoto'

    params = {
        'access_token': token,
        'v': version,
        'group_id': group_id,
        'photo': photo,
        'server': server,
        'hash': response_hash
    }

    response = requests.post(url, params=params)
    response.raise_for_status()
    check_response(response.json())

    upload_response = response.json()['response'][0]

    owner_id = upload_response['owner_id']
    media_id = upload_response['id']

    return owner_id, media_id


def publish_comic_to_group(token, version, group_id, owner_id, media_id, comment):

    url = 'https://api.vk.com/method/wall.post'

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
    check_response(response.json())


def check_response(response):
    if "error" in response:
        message = response["error"]["error_msg"]
        error_code = response["error"]["error_code"]
        raise requests.HTTPError(error_code, message)


def main():

    load_dotenv()

    version = 5.131
    vk_access_token = os.getenv('VK_ACCESS_TOKEN')
    group_id = int(os.getenv('VK_GROUP_ID'))
    try:
        image_url, comment, title = generate_random_comic()
        filename = save_image(title, image_url)
        upload_url = get_upload_url(vk_access_token, version, group_id)
        server, response_hash, photo = upload_image_to_server(upload_url, filename)
        owner_id, media_id = upload_comic_to_wall(vk_access_token, version, group_id, server, response_hash, photo)
        publish_comic_to_group(vk_access_token, version, group_id, owner_id, media_id, comment)
    finally:
        os.remove(filename)


if __name__ == "__main__":
    main()