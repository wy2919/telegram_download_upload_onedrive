# !/usr/bin/env python3
import difflib
import os
import platform
import re
import time
import asyncio
import asyncio.subprocess
import logging
import uuid

import telethon
from telethon import TelegramClient, events, errors
from telethon.tl.types import MessageMediaWebPage, PeerChannel, InputMessagesFilterPhotos, InputMessagesFilterVideo, \
    InputMessagesFilterPhotoVideo
import cryptg

# 导入的另一个py文件中的方法
from mysql_test import get
from mysql_test import set

# github : https://github.com/snow922841/telegram_channel_downloader

# ***********************************************************************************#
# 去这里创建应用获取api_id 和api_hash https://my.telegram.org/apps
api_id = 14912421  # api ID
api_hash = '03e02666b77ced60cab759d4c31c488d'  # api hash
bot_token = '5285482606:AAHIerhotb28ozU1L3UCS4kyfFLNZM3PA7o'  # bot_token
admin_id = 1762277767  # 我的id  去这个机器人获取：@getidsbot
upload_file_set = True  # 是否上传网盘
max_num = 20  # 同时下载数量
# filter file name/文件名过滤
filter_list = ['你好，欢迎加入 Quantumu', '\n']
# filter chat id /过滤某些频道不下载
blacklist = [1388464914, ]
download_all_chat = False  # 监控所有你加入的频道，收到的新消息如果包含媒体都会下载，默认关闭
filter_file_name = []  # 过滤文件后缀，可以填jpg、avi、mkv、rar等。
proxy = ("HTTP", '127.0.0.1', 1082)  # 自行替换代理设置，如果不需要代理，请删除括号内容
# ***********************************************************************************#

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.WARNING)
logger = logging.getLogger(__name__)
queue = asyncio.Queue()

# 当前第几个消息
dq = 0

# 客户端id
K_ID = 1

# 要下载的文件格式
accept_file_format = ["image/jpeg", "image/gif", "image/png", 'video/mp4']

# 根据客户端不同路径也不同
sysstr = platform.system()
if (sysstr == "Windows"):
    save_path = r'file'
elif (sysstr == "Linux"):
    save_path = r'/home'


# 文件夹/文件名称处理
def validate_title(title):
    r_str = r"[\/\\\:\*\?\"\<\>\|\n]"  # '/ \ : * ? " < > |'
    new_title = re.sub(r_str, "_", title)  # 替换为下划线
    return new_title


# 获取相册标题
async def get_group_caption(message):
    group_caption = ""
    entity = await client.get_entity(message.to_id)
    async for msg in client.iter_messages(entity=entity, reverse=True, offset_id=message.id - 9, limit=10):
        if msg.grouped_id == message.grouped_id:
            if msg.text != "":
                group_caption = msg.text
                return group_caption
    return group_caption


# 获取本地时间
def get_local_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# 判断相似率
def get_equal_rate(str1, str2):
    return difflib.SequenceMatcher(None, str1, str2).quick_ratio()


# 返回文件大小
def bytes_to_string(byte_count):
    suffix_index = 0
    while byte_count >= 1024:
        byte_count /= 1024
        suffix_index += 1

    return '{:.2f}{}'.format(
        byte_count, [' bytes', 'KB', 'MB', 'GB', 'TB'][suffix_index]
    )


# 下载方法
async def worker(name):
    # 一直循环从队列获取任务
    while True:

        # 获取任务
        queue_item = await queue.get()

        # 取出要下载的消息
        message = queue_item[0]

        # 取出频道名称
        chat_title = queue_item[1]

        # 取出频道实体
        entity = queue_item[2]

        # 根据实体获取频道id
        chat_id = entity.id

        # 取出文件名
        file_name = queue_item[3]

        # 取出文件id
        file_id = queue_item[4]

        # 取出频道名称
        chat_title = queue_item[5]

        print(f"{name}  {get_local_time()} 开始下载： {chat_title} - {file_name} - {str(message.id)}")

        file_type = str(os.path.splitext(file_name)[-1]).split('.')[1]

        # 拼接文件保存路径
        # file_save_path = file_name
        file_save_path = save_path + '/' + chat_title + '/' + file_type + '/' + file_name

        try:
            # loop = asyncio.get_event_loop()
            # # 开启下载
            task = loop.create_task(client.download_media(message, file_save_path))
            # 等待阻塞 等待下载
            await asyncio.wait_for(task, timeout=1200)
            # os.close(file_save_path)


            # 插入数据库
            pd = set(file_type, file_name, file_save_path, chat_title,chat_id, file_id)

        except (errors.rpc_errors_re.FileReferenceExpiredError, asyncio.TimeoutError):
            logging.warning(f'{get_local_time()} - {file_name} 出现异常，重新尝试下载！')
            async for new_message in client.iter_messages(entity=entity, offset_id=message.id - 1, reverse=True,
                                                          limit=1):
                await queue.put((new_message, chat_title, entity, file_name))
        except Exception as e:
            print(f"{get_local_time()} - {file_name} {e.__class__} {e}")
            await bot.send_message(admin_id, f'{e.__class__}!\n\n{e}\n\n{file_name}')
        finally:
            queue.task_done()



            # 关闭文件
            # os.close(file_save_path)


# 接受到/sl  查询队列数量
@events.register(events.NewMessage(pattern='/sl' + str(K_ID), from_users=admin_id))
async def get_size(update):
    await bot.send_message(admin_id, f'任务队列数量：{queue.qsize()} 消息id：{str(dq)}')


# 接受到/start
@events.register(events.NewMessage(pattern='/start' + str(K_ID), from_users=admin_id))
async def handler(update):
    # tg接受到的命令 ：/start https://t.me/chigua91 10
    # 分割好
    text = update.message.text.split(' ')
    msg = '参数错误，请按照参考格式输入:\n\n' \
          '1.普通群组\n' \
          '<i>/start https://t.me/fkdhlg 0 </i>\n\n' \
          '2.私密群组(频道) 链接为随便复制一条群组消息链接\n' \
          '<i>/start https://t.me/12000000/1 0 </i>\n\n' \
          'Tips:如果不输入offset_id，默认从第一条开始下载'
    if len(text) == 1:
        # 命令错误 返回消息
        await bot.send_message(admin_id, msg, parse_mode='HTML')
        return
    elif len(text) == 2:
        # 没有从第几个开始，默认从0开始 全部下载

        # 获取到频道链接：https://t.me/chigua91
        chat_id_name = text[1]
        offset_id = 0
        try:
            # 根据链接获取频道实体
            entity = await client.get_entity(chat_id_name)
            # 获取频道名称
            chat_title = entity.title

            # 返回消息 回复上一条
            await update.reply(f'开始从 {chat_title} 的第 {0} 条消息下载')
        except ValueError:
            # https://t.me/12000000/1  这样格式的链接获取频道id
            channel_id = text[1].split('/')[4]
            # 根据id获取频道实体
            entity = await client.get_entity(PeerChannel(int(channel_id)))
            # 获取频道名称
            chat_title = entity.title

            # 返回消息 回复上一条
            await update.reply(f'开始从 {chat_title} 的第 {0} 条消息下载')
        except Exception as e:
            await update.reply('chat输入错误，请输入频道或群组的链接\n\n'
                               f'错误类型：{e.__class__}'
                               f'异常消息：{e}')
            return
    elif len(text) == 3:
        # 获取到频道链接：https://t.me/chigua91
        chat_id_name = text[1]
        # 从第几个开始下载
        offset_id = int(text[2])
        try:
            # 获取频道实体
            entity = await client.get_entity(chat_id_name)
            # 获取频道名称
            chat_title = entity.title

            # 回复消息
            await update.reply(f'开始从 {chat_title} 的第 {offset_id} 条消息下载')
        except ValueError:
            # https://t.me/12000000/1  这样格式的链接获取频道id
            channel_id = text[1].split('/')[4]
            # 根据id获取频道实体
            entity = await client.get_entity(PeerChannel(int(channel_id)))
            # 获取频道名称
            chat_title = entity.title

            # 返回消息 回复上一条
            await update.reply(f'开始从 {chat_title} 的第 {offset_id} 条消息下载')
        except Exception as e:
            await update.reply('chat输入错误，请输入频道或群组的链接\n\n'
                               f'错误类型：{type(e).__class__}'
                               f'异常消息：{e}')
            return
    else:
        # 输入错误 返回
        await bot.send_message(admin_id, msg, parse_mode='HTML')
        return

    chat_title = validate_title(chat_title)

    # 频道名称
    if chat_title:
        print(f'{get_local_time()} - 开始下载：{chat_title}({entity.id}) - {offset_id}')

        # 获取频道的消息 参数1：频道实体 参数2：从第几个消息开始获取 reverse（True/False）：true从最久远的消息到现在 false从现在往之前获取
        # filter：消息过滤器（只获取照片和视频），详情：https://tl.telethon.dev/constructors/input_messages_filter_photos.html
        async for message in client.iter_messages(entity, offset_id=offset_id, reverse=True, limit=None,
                                                  filter=InputMessagesFilterPhotoVideo):

            # 监听任务队列长度 因为一个频道有的好几万消息 不可能全部加入到队列
            # 只能一次加入多少 然后等待队列中的任务消耗完毕在继续添加
            if queue.qsize() == 10:
                # 阻塞调用线程，直到队列中的所有任务被处理掉。
                await queue.join()
                dq = message.id
                print("继续获取任务......................")


            # 判断是否是媒体类型
            if message.media:
                # 如果是媒体

                # 获取媒体类型
                is_webpage = isinstance(message.media, telethon.tl.types.MessageMediaWebPage)
                is_photo = isinstance(message.media, telethon.tl.types.MessageMediaPhoto)
                is_doc = isinstance(message.media, telethon.tl.types.MessageMediaDocument)

                # print(message.media)

                # 判断媒体是否是受支持的
                if not is_photo:  # 不是照片 一定是文件或者是网页
                    if is_doc:  # 如果是文件 判断文件类型
                        is_accept_media = message.media.document.mime_type in accept_file_format  # 检查文件类型是否属于支持的文件类型

                        if not is_accept_media:  # 判断文件类型是否是需要的类型
                            print("不接受的媒体类型------------------ ")
                            continue
                    else:
                        # 不是文件 就是网页不下载
                        print("不接受的媒体类型------------------ ")
                        continue

                # 获取文件的id 来到这里的一定是照片或者是受支持的文件
                if is_photo:
                    file_id = message.media.photo.id
                else:
                    # file_size = message.media.document.size
                    file_id = message.media.document.id

                # 查询数据库 没有下载过才下载
                if get(file_id):
                    # 生成文件名 不含后缀
                    caption = ''.join(str(uuid.uuid4()).split('-'))

                    file_name = ''

                    # 如果是文件
                    if message.document:
                        # 遍历获取原始文件名
                        for i in message.document.attributes:
                            try:
                                file_name = i.file_name
                            except:
                                continue
                        # 如果获取不到原始文件名 也就是获取不到后缀 就从类型中获取后缀
                        if file_name == '':
                            file_name = f'{caption}.{message.document.mime_type.split("/")[-1]}'
                        else:
                            # 获取到了原始文件名 使用方法获取后缀
                            hz = os.path.splitext(file_name)[-1]
                            # 拼接文件名
                            file_name = caption + hz
                    elif message.photo:
                        # 图片直接返回文件名
                        file_name = f'{caption}.jpg'
                    else:
                        continue

                    print("添加进")

                    # 添加进队列 参数1：要下载的消息 参数2：频道标题  参数3：频道实体 参数4：文件名 参数5：文件id 参数6：频道名称
                    await queue.put((message, chat_title, entity, file_name, file_id, chat_title))
                    # else:
                    #     print()
                    # print("已上传跳过："+str(file_id))

        await bot.send_message(admin_id, f'{chat_title} 所有消息添加到任务队列 数量：{queue.qsize()}')


@events.register(events.NewMessage())
async def all_chat_download(update):
    message = update.message
    if message.media:
        chat_id = update.message.to_id
        entity = await client.get_entity(chat_id)
        if entity.id in blacklist:
            return
        chat_title = entity.title

        # 生成文件名 不含后缀
        caption = ''.join(str(uuid.uuid4()).split('-'))

        file_name = ''
        # 如果是文件
        if message.document:
            try:
                if type(message.media) == MessageMediaWebPage:
                    return
                if message.media.document.mime_type == "image/webp":
                    file_name = f'{message.media.document.id}.webp'
                if message.media.document.mime_type == "application/x-tgsticker":
                    file_name = f'{message.media.document.id}.tgs'
                for i in message.document.attributes:
                    try:
                        file_name = i.file_name
                    except:
                        continue
                if file_name == '':
                    file_name = f'{message.id} - {caption}.{message.document.mime_type.split("/")[-1]}'
                else:
                    # 如果文件名中已经包含了标题，则过滤标题
                    if get_equal_rate(caption, file_name) > 0.6:
                        caption = ""
                    file_name = f'{message.id} - {caption}{file_name}'
            except:
                print(message.media)
        elif message.photo:
            file_name = f'{message.id} - {caption}{message.photo.id}.jpg'
        else:
            return
        # 过滤文件名称中的广告等词语
        for filter_keyword in filter_list:
            file_name = file_name.replace(filter_keyword, "")
        print(chat_title, file_name)
        await queue.put((message, chat_title, entity, file_name))


if __name__ == '__main__':

    # 根据客户端不同决定是否使用代理
    # 监听频道获取消息机器人办不了只能使用自己
    if (sysstr == "Windows"):
        # 机器人
        bot = TelegramClient('telegram_channel_downloader_bot',
                             api_id, api_hash, proxy=proxy).start(bot_token=str(bot_token))
        # 自己
        client = TelegramClient(
            'telegram_channel_downloader', api_id, api_hash, proxy=proxy).start(password='150530wang')
    elif (sysstr == "Linux"):
        # 机器人
        bot = TelegramClient('telegram_channel_downloader_bot',
                             api_id, api_hash).start(bot_token=str(bot_token))
        # 自己
        client = TelegramClient(
            'telegram_channel_downloader', api_id, api_hash).start(password='150530wang')

    # 添加监听方法
    bot.add_event_handler(get_size)
    bot.add_event_handler(handler)

    # 是否监听所有频道
    if download_all_chat:
        client.add_event_handler(all_chat_download)
    tasks = []

    # 开启多个线程进行下载 监听队列中有没有任务
    try:
        for i in range(max_num):
            loop = asyncio.get_event_loop()
            task = loop.create_task(worker(f'线程：-{i}'))
            tasks.append(task)
        print('成功启动........')

        # 阻塞不让退出
        client.run_until_disconnected()
    finally:
        # 线程批量等待
        for task in tasks:
            task.cancel()
        client.disconnect()
        print('Stopped!')
