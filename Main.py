import vk_api
import requests
import time
from flask import Flask, request, json, make_response, jsonify
from settings import *

resend_bot_session = vk_api.VkApi(token=resend_bot_token)
app = Flask(__name__)


@app.route('/')
def page():  # отображается на сайте приложения
    return 'Страничка бота-пересыльщика'


def send_msg(session, user_id, s):
    session.method('messages.send', {'peer_id': user_id, 'message': s})


def private_crate(text, peer):  # функция создания канала для личных сообщений
    sms = 'Произошла неизвестная ошибка, попробуйте ещё раз или обратитесь к разработчику!'
    if len(text) != 2:
        sms = 'Передано не верное количество параметров!'
    else:
        if text[0].isnumeric():
            data = {
                "bot": "vk",
                "tgid": int(text[0]),
                "vkid": int(peer),
                "tgname": str(text[1]),
                "vkname": "none"
            }
            response = (requests.post(url=create_url, json=data)).json()  # передача данных микросервису базы данных и получение ответа
            if 'succ' in response.keys():
                if response['succ'] == 'data updated':
                    sms = 'Канал иницирован.'
            elif 'error' in response.keys():
                if response['error'] == 'bad request':
                    sms = 'Ошибка входных данных!'
                elif response['error'] == 'server error':
                    sms = 'Произошла ошибка базы данных!'
        else:
            sms = 'id не может состоять из букв. Смотри /help'
    send_msg(resend_bot_session, peer, sms)


def private_list(peer):  # функция получения списка контактов
    sms = 'Произошла неизвестная ошибка, попробуйте ещё раз или обратитесь к разработчику!'
    data = {
        "bot": "vk",
        "tgid": 0,
        "vkid": int(peer),
        "tgname": "none",
        "vkname": "none"
    }
    respons = (
        requests.post(url=list_url, json=data)).json()  # передача данных микросервису базы данных и получение ответа
    if 'data' in respons.keys():
        sms = ''
        if len(respons['data']) != 0:
            for item in respons['data']:
                sms = sms + item + '\n'
        else:
            sms = 'Ваш список контактов пуст. Возможно каналы ожидают подтверждения'
    elif 'error' in respons.keys():
        if respons['error'] == 'no channel':
            sms = 'Канал не существует, или ожидает подтверждения!'
        elif respons['error'] == 'channel wait':
            sms = 'Канал ожидает подтверждения собеседника'
        elif respons['error'] == 'bad request':
            sms = 'Ошибка входных данных!'
        elif respons['error'] == 'server error':
            sms = 'Произошла ошибка базы данных!'
    send_msg(resend_bot_session, peer, sms)


def private_info(name, peer):  # фунция получения id
    data = {
        "bot": "vk",
        "tgid": 0,
        "vkid": int(peer),
        "tgname": str(name),
        "vkname": "none"
    }
    respons = (
        requests.post(url=info_url, json=data)).json()  # передача данных микросервису базы данных и получение ответа
    if 'tgid' in respons.keys():
        info = {}
        info['id'] = int(respons['tgid'])
        info['name'] = str(respons['vkname'])
        return info
    elif 'error' in respons.keys():
        return respons


def private_delete(text, peer):  # функция создания канала
    sms = 'Произошла неизвестная ошибка, попробуйте ещё раз или обратитесь к разработчику!'
    if len(text) != 1:
        return 'Передано не верное количество параметров!'
    else:
        data = {
            "bot": "vk",
            "tgid": 0,
            "vkid": int(peer),
            "tgname": str(text[0]),
            "vkname": "none"
        }
    respons = (
        requests.post(url=delete_url, json=data)).json()  # передача данных микросервису базы данных и получение ответа
    if 'succ' in respons.keys():
        if respons['succ'] == 'deleted':
            sms = 'Канал успешно удалён. Или никогда не существовал.'
    elif 'error' in respons.keys():
        if respons['error'] == 'bad request':
            sms = 'Ошибка входных данных!'
        elif respons['error'] == 'server error':
            sms = 'Произошла ошибка базы данных!'
    send_msg(resend_bot_session, peer, sms)


def private_send(text, peer, attachment_list, resend_string):  # Функция отправки сообщений
    sms = 'Произошла неизвестная ошибка, попробуйте ещё раз или обратитесь к разработчику!'
    flag = 0
    name = text[0]
    respons = private_info(name, peer)
    if 'id' in respons.keys():
        message = '#' + respons['name'] + ':\n' + ' '.join(text[1:]) + '\n\n'
        if len(attachment_list) != 0:
            for link in attachment_list:
                message = message + '\n' + link + '\n'
        if len(resend_string) != 0:
            message = message + resend_string
        data = {
            "tgid": respons['id'],
            "message": message
        }
        respons = (
            requests.post(url=tg_url, json=data)).json()  # передача данных боту telegram
        if 'succ' not in respons.keys():
            sms = 'Шо-то пошло не так'
        else:
            resend_bot_session.method('messages.markAsRead',
                                      {'peer_id': peer})  # если сообщение не из беседы - читаем его
            flag = 1
    elif 'error' in respons.keys():
        if respons['error'] == 'no channel':
            sms = 'Канал не существует, или ожидает подтверждения!'
        elif respons['error'] == 'channel wait':
            sms = 'Канал ожидает подтверждения собеседника'
        elif respons['error'] == 'bad request':
            sms = 'Ошибка входных данных!'
        elif respons['error'] == 'server error':
            sms = 'Произошла ошибка базы данных!'
        elif respons['error'] == 'channel exist':
            sms = 'У этого чата уже есть канал'
    if flag == 0:
        send_msg(resend_bot_session, peer, sms)


def group_crate(text, peer):
    sms = 'Произошла неизвестная ошибка, попробуйте ещё раз или обратитесь к разработчику!'
    if len(text) != 1:
        sms = 'Передано не верное количество параметров!'
    else:
        data = {
            "bot": "vk",
            "tgid": int(text[0]),
            "vkid": int(peer)
        }
        response = (requests.post(url=group_create_url,
                                  json=data)).json()  # передача данных микросервису базы данных и получение ответа
        if 'succ' in response.keys():
            sms = 'succ'
            if response['succ'] == 'data updated':
                sms = 'Канал инициирован'
        elif 'error' in response.keys():
            sms = response['error']
            if response['error'] == 'bad request':
                sms = 'Ошибка входных данных!'
            elif response['error'] == 'server error':
                sms = 'Произошла ошибка базы данных!'
            elif response['error'] == 'channel exist':
                sms = 'У этого чата уже есть канал'
    send_msg(resend_bot_session, peer, sms)


def group_info(peer):  # фунция получения id
    data = {
        "bot": "vk",
        "tgid": 0,
        "vkid": int(peer)
    }
    respons = (requests.post(url=group_info_url,
                             json=data)).json()  # передача данных микросервису базы данных и получение ответа
    if 'tgid' in respons.keys():
        info = {}
        info['id'] = int(respons['tgid'])
        return info
    if 'error' in respons.keys():
        return respons


def group_delete(peer):  # функция создания канала
    sms = 'Произошла неизвестная ошибка, попробуйте ещё раз или обратитесь к разработчику!'
    data = {
        "bot": "vk",
        "tgid": 0,
        "vkid": int(peer)
    }
    respons = (requests.post(url=group_delete_url,
                             json=data)).json()  # передача данных микросервису базы данных и получение ответа
    if 'succ' in respons.keys():
        if respons['succ'] == 'deleted':
            sms = 'Канал успешно удалён. Или никогда не существовал.'
    if 'error' in respons.keys():
        if respons['error'] == 'bad request':
            sms = 'Ошибка входных данных!'
        elif respons['error'] == 'server error':
            sms = 'Произошла ошибка базы данных!'
    send_msg(resend_bot_session, peer, sms)


def group_send(text, peer, who, attachment_list, resend_string):
    sms = 'Произошла неизвестная ошибка, попробуйте ещё раз или обратитесь к разработчику!'
    flag = 0
    respons = group_info(peer)
    user = resend_bot_session.method('users.get', {'user_ids': who})  # получаем информацию о пользвателе
    user = '#' + user[0].setdefault('first_name') + '_' + user[0].setdefault('last_name')  # записываем имя пользователя
    if 'id' in respons.keys():
        message = user + ':\n' + ' '.join(text[0:]) + '\n\n'
        if len(attachment_list) != 0:
            for link in attachment_list:
                message = message + '\n' + link + '\n'
        if len(resend_string) != 0:
            message = message + resend_string
        data = {
            "tgid": respons['id'],
            "message": message
        }
        respons = (requests.post(url=tg_url,
                                 json=data)).json()  # передача данных боту telegram
        if 'succ' not in respons.keys():
            sms = 'Шо-то пошло не так'
        else:
            flag = 1
    if 'error' in respons.keys():
        if respons['error'] == 'no channel':
            sms = 'Канал не существует, или ожидает подтверждения!'
        elif respons['error'] == 'channel wait':
            sms = 'Канал ожидает подтверждения собеседника'
        elif respons['error'] == 'bad request':
            sms = 'Ошибка входных данных!'
        elif respons['error'] == 'server error':
            sms = 'Произошла ошибка базы данных!'
    if flag == 0:
        send_msg(resend_bot_session, peer, sms)


def attach_type(attachment, arr_urls):
    for attach in attachment:
        if attach['type'] == 'photo':
            photo_arr = {}
            for item in attach['photo']['sizes']:
                photo_arr[item['type']] = item['url']
            if 'w' in photo_arr.keys():
                arr_urls.append(photo_arr['w'] + '\n')
            elif 'z' in photo_arr.keys():
                arr_urls.append(photo_arr['z'] + '\n')
            elif 'y' in photo_arr.keys():
                arr_urls.append(photo_arr['y'] + '\n')
            elif 'x' in photo_arr.keys():
                arr_urls.append(photo_arr['x'] + '\n')
            elif 'm' in photo_arr.keys():
                arr_urls.append(photo_arr['m'] + '\n')
            elif 's' in photo_arr.keys():
                arr_urls.append(photo_arr['s'] + '\n')
            elif 'r' in photo_arr.keys():
                arr_urls.append(photo_arr['r'] + '\n')
            elif 'q' in photo_arr.keys():
                arr_urls.append(photo_arr['q'] + '\n')
            elif 'p' in photo_arr.keys():
                arr_urls.append(photo_arr['p'] + '\n')
            elif 'o' in photo_arr.keys():
                arr_urls.append(photo_arr['o'] + '\n')

        if attach['type'] == 'video':
            # print(attach)
            # arr_urls.append(attach['video']['player'])
            # id_video = attach['video']['id']
            # video_owner_id = attach['video']['owner_id']
            # video_access_key = attach['video']['access_key']
            # key = str(id_video) + '_' + str(video_owner_id) + '_' + str(video_access_key)
            # print(resend_bot_session.method('video.get', {'videos': key})) #  нельзя использовать такой запрос с сервера - ограничение api
            pass
        if attach['type'] == 'audio':
            arr_urls.append(attach['audio']['url'] + '\n')
        if attach['type'] == 'doc':
            arr_urls.append(attach['doc']['url'] + '\n')
        if attach['type'] == 'sticker':
            arr_urls.append(attach['sticker']['images_with_background'][4]['url'] + '\n')
    return arr_urls


def resend_messages(messages_list, result):
    for message in messages_list:
        attachment_list = []
        if message['attachments']:
            attachment_list = attach_type(message['attachments'], [])
        if message['from_id'] > 0:
            user = resend_bot_session.method('users.get',
                                             {'user_ids': message['from_id']})  # получаем информацию о пользвателе
            user = user[0].setdefault('first_name') + ' ' + user[0].setdefault(
                'last_name')  # записываем имя пользователя
            result = result + 'Пересланное сообщение от ' + user + ':\n'
            if message['text']:
                result = result + message['text'] + '\n\n'
            if len(attachment_list) != 0:
                for link in attachment_list:
                    result = result + '\n' + link + '\n'
        if 'fwd_messages' in message.keys():
            result = resend_messages(message['fwd_messages'], result)
    return result


def resend_bot(data):  # тело бота, пересылающего сообщения
    peer = data['object']['peer_id']
    who = data['object']['from_id']
    text = data['object']['text'].replace('\n', ' ').split(' ')
    resend_string = ''
    if data['object']['fwd_messages']:
        resend_string = resend_messages(data['object']['fwd_messages'], '')
    attachment_list = []
    if data['object']['attachments']:
        attachment_list = attach_type(data['object']['attachments'], attachment_list)
    if who > 0:  # если сообщение отправлено не ботом
        if who == peer:  # если это личное сообщение
            if text[0] == '/help':
                sms = 'В запросах пробел между параметрами обязателен!  Не используйте пробелы в имени собеседника.\n\n' \
                      '/id - показывает ваш id для создания канала. Передайте его собеседнику из telegram\n\n' \
                      '/create - создать канал для общения. Для этого вам нужно узнать telegram id вашего собеседника\nПример:\n' \
                      '/create 00000 Иванов_Пётр\n\n' \
                      '/list - список собеседников. (Только подтвеждённые каналы)\n\n' \
                      '/delete - удаляет существующий канал\n' \
                      'Пример:\n /delete Иванов_Пётр\n\n' \
                      'Для отправки сообщения первым словом напишите имя вашего собеседника\n' \
                      'Пример:\n' \
                      '/Иванов_Пётр текст вашего сообщения'
                send_msg(resend_bot_session, peer, sms)
            elif text[0] == '/id':
                send_msg(resend_bot_session, peer, str(peer))
            elif text[0] == '/create':
                private_crate(text[1:], peer)
            elif text[0] == '/list':
                private_list(peer)
            elif text[0] == '/delete':
                private_delete(text[1:], peer)
            else:
                private_send(text, peer, attachment_list, resend_string)
        if who != peer:  # Если это сообщение в беседе
            if text[0] == '/help':
                sms = 'В запросах пробел между параметрами обязателен!\n\n' \
                      '/id - показывает ваш id для создания канала. Передайте его собеседнику из telegram\n\n' \
                      '/create - создать канал для общения. Для этого вам нужно узнать telegram id чата\nПример:\n' \
                      '/create 00000\n\n' \
                      '/delete - удаляет существующий канал\n' \
                      'Пример:\n /delete'
                send_msg(resend_bot_session, peer, sms)
            elif text[0] == '/id':
                send_msg(resend_bot_session, peer, str(peer))
            elif text[0] == '/create':
                group_crate(text[1:], peer)
            elif text[0] == '/delete':
                group_delete(peer)
            else:
                group_send(text, peer, who, attachment_list, resend_string)


@app.route('/', methods=['POST'])
def processing():
    data = json.loads(request.data)  # Распаковываем json из пришедшего POST-запроса
    if data['type'] == 'confirmation':
        return resend_bot_confirmation_token
    elif data['type'] == 'message_new':
        resend_bot(data)
    return 'ok'  # Сообщение о том, что обработка прошла успешно


@app.route('/incoming', methods=['POST'])
def incoming():
    data = request.json  # Распаковываем json из пришедшего POST-запроса
    # print(data)
    send_msg(resend_bot_session, data['vkid'], data['message'])
    return make_response(jsonify({"succ": "message send"}), 200)