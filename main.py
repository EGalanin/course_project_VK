import os.path
import requests
from pprint import pprint
import json
import time
from tqdm import tqdm

with open('token.txt', 'r') as f:
    token_vk = f.read().strip()

with open('token_ya.txt', 'r') as f:
    token_ya = f.read().strip()


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version,
        }

    def get_foto(self, id):
        """
        Получение данных С ВК методом 'photos.get'
        param: id:
        return: список  photos_list
        """
        url_foto = self.url + 'photos.get'
        groups_info_params = {
            'owner_id': id,
            'album_id': 'profile',
            'extended': 1,
            'photo_sizes': 1,
            'count': 5
        }
        req = requests.get(url_foto, params={**self.params, **groups_info_params}).json()
        # pprint(req)
        photos_list = []
        repeat_likes = {}
        for value in req['response']['items']:
            if value['likes']['count'] in repeat_likes:
                repeat_likes[value['likes']['count']] += 1
            else:
                repeat_likes[value['likes']['count']] = 1
        # print(repeat_likes)
        for value in tqdm(req['response']['items'], desc='Получение фото от ВК', ncols=90):
            # Определение самой большой фотографии: сортировка списка фотографий по высоте и ширине
            file_params = sorted(value['sizes'], key=lambda x: x['height'] + x['width'], reverse=True)[0]
            # Создание имени фотографии в формате: id_likes.jpg
            if repeat_likes.get(value['likes']['count'], 0) > 1:
                file_params['file_name'] = str(value['likes']['count']) + '_' + str(value['date']) + '.jpg'
            else:
                file_params['file_name'] = str(value['likes']['count']) + '.jpg'
            photos_list.append(file_params)
            time.sleep(1)
        # pprint(photos_list)
        for value in photos_list:
            del value['height']
            del value['width']
            value['size'] = value.pop('type')
        # pprint(photos_list)
        return photos_list

        # Данный способ не получает фото мах размера
        # for value in req['response']['items']:
        #     photo_dict = {
        #         'file_name': f"{value['likes']['count']}_{value['date']}.jpg",
        #         'size': value['sizes'][-1]['type'],
        #         'url': value['sizes'][-1]['url']}
        #     photos_list.append(photo_dict)
        # pprint(photos_list)


class YaDiskUser:
    def __init__(self, token):
        self.url_upload_file = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def get_folder(self, disk_path):
        """
        Создание папки на Яндекс диск методом put
        param: disk_path
        return: disk_path
        """
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = self.get_headers()
        params = {"path": disk_path, "overwrite": "true"}
        res = requests.put(url, headers=headers, params=params)
        # pprint(res.status_code)
        # print(disk_path)
        return disk_path

    def get_upload_link(self, disk_path, filename):
        headers = self.get_headers()
        params = {"path": self.get_folder(disk_path) + '/' + filename, "overwrite": "true"}
        res = requests.get(self.url_upload_file, headers=headers, params=params).json()
        # pprint(res)
        return res

    def upload_file_to_disk(self, disk_path, filename):
        href_json = self.get_upload_link(disk_path, filename)
        href = href_json['href']
        # print(href)
        # pprint(href_json)
        res = requests.put(href, data=open(filename, 'rb'))
        res.raise_for_status()
        if res.status_code == 201:
            print("Success")

    def upload_url_to_disk(self, disk_path):
        """
        Загрузка файла на Яндекс диск методом post
        disk_path: путь к папке на Яндекс диске
        url: ссылка на файл в ВК
        """
        for i in tqdm(foto, desc='Загрузка фото на ЯД', ncols=90):
            headers = self.get_headers()
            params = {"path": self.get_folder(disk_path) + '/' + i['file_name'], "url": i['url'],
                      "overwrite": "true"}
            res = requests.post(url=self.url_upload_file, headers=headers, params=params)
            if res.status_code == 202:
                continue
            else:
                print(res)
            time.sleep(1)
        print('Фото успешно загруженны')


if __name__ == '__main__':
    vk = VkUser(token=token_vk, version=5.131)
    id = input('Введите ID пользователя VK: ')  # тест ID 552934290
    foto = vk.get_foto(id=id)
    with open('VK_photo.json', 'w', encoding='utf-8') as file:  # Сохранение JSON списка в файл
        json.dump(foto, file, ensure_ascii=False, indent=4)
    ya = YaDiskUser(token=token_ya)
    ya.upload_url_to_disk('Foto_VK')
    ya.upload_file_to_disk('Foto_VK', 'VK_photo.json')
