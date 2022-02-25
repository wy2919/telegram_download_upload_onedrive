import asyncio
import os
import re
from time import sleep, time
import functools

import requests
from tqdm import tqdm
import msal
import uuid


# 获取直链 就是为分享链接加一个：?download=1
async def getUrl(headers, file_id):
    url = 'https://graph.microsoft.com/v1.0/me/drive/items/' + file_id + '/createLink'

    # 协程异步请求 阻塞会自动切换
    future = asyncio.get_event_loop().run_in_executor(None, functools.partial(requests.post,url,data={
        "type": "embed",
        "scope": "anonymous"
    }, headers=headers))

    r = await future

    # 根据文件的id获取文件的分享链接 并拼接为直链
    # r = requests.post(url, data={
    #     "type": "embed",
    #     "scope": "anonymous"
    # }, headers=headers)

    try:
        # print("上传成功")
        return r.json()['link']['webUrl'] + '?download=1'
    except Exception as e:
        print('发生错误.........')
        print(e)
        return ''

async def getToken(CLIENT_ID, TENANT_ID, USERNAME, PASSWORD):
    AUTHORITY_URL = 'https://login.microsoftonline.com/{}'.format(TENANT_ID)

    # 权限
    SCOPES = ['Sites.ReadWrite.All', 'Files.ReadWrite.All']

    # 登录认证获取access_token
    cognos_to_onedrive = msal.PublicClientApplication(CLIENT_ID, authority=AUTHORITY_URL)
    token = cognos_to_onedrive.acquire_token_by_username_password(USERNAME, PASSWORD, SCOPES)
    try:
        access_token = token['access_token']
        headers = {'Authorization': 'Bearer {}'.format(access_token)}
        return headers
    except Exception as e:
        print("登录错误：" + token['error_uri'])
        exit()


async def upload(headers, file_path,name,type):
    RESOURCE_URL = 'https://graph.microsoft.com/'
    API_VERSION = 'v1.0'


    # time_str = datetime.datetime.now().strftime('%m-%d_%H_%M_%S')


    onedrive_destination = '{}/{}/me/drive/root:/tg/{}/{}'.format(RESOURCE_URL, API_VERSION,name,type)


    file_name = ''.join(str(uuid.uuid4()).split('-')) + os.path.splitext(file_path)[-1]
    file_size = os.stat(file_path).st_size
    file_data = open(file_path, 'rb')

    return_data = {
        'file_name':file_name,
        'file_path': '/tg/{}/{}/{}'.format(name,type,file_name)
    }


    # 小于4M直接上传 大于就分片上传
    if file_size < 4100000:
        try:
            # 协程异步请求 阻塞会自动切换
            future = asyncio.get_event_loop().run_in_executor(None, functools.partial(requests.put,onedrive_destination + "/" + file_name + ":/content",data=file_data, headers=headers))


            r = await future
            # r = requests.put(onedrive_destination + "/" + file_name + ":/content", data=file_data, headers=headers)
            s = r.json()
            # print(s)
            # 正则表达式提取文件ID
            file_id = re.findall('(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})', s['eTag'])
            url = await getUrl(headers, file_id[0])
            file_data.close()
            return_data['url'] = url
            return return_data
        except Exception as e:
            print('发生错误.........')
            print(e)
            return ''
    else:
        try:
            # 创建分片上传会话 返回分片上传的url
            upload_session = requests.post(onedrive_destination + "/" + file_name + ":/createUploadSession",
                                           headers=headers).json()

            with open(file_path, 'rb') as f:
                # 获取文件总大小
                total_file_size = os.path.getsize(file_path)

                # 一次分片的大小 50M
                chunk_size = 155000000
                chunk_number = total_file_size // chunk_size
                chunk_leftover = total_file_size - chunk_size * chunk_number
                i = 0
                for i in tqdm(range(chunk_number + 1)):
                    # 读取
                    chunk_data = f.read(chunk_size)
                    # 本次上传的开始字节 当前次数 * 一次上传大小
                    start_index = i * chunk_size
                    # 本次上传的结束字节
                    end_index = start_index + chunk_size

                    # 读取不到结束循环
                    if not chunk_data:
                        break
                    # 最后一次 字节不是完整的
                    if i == chunk_number:
                        end_index = start_index + chunk_leftover

                    # 拼接headers 分片上传
                    # Content-Length ：总大小
                    # Content-Range： bytes 开始字节-结束字节/总字节
                    headers2 = {'Content-Length': '{}'.format(chunk_size),
                               'Content-Range': 'bytes {}-{}/{}'.format(start_index, end_index - 1,
                                                                        total_file_size)}
                    # loop = asyncio.get_event_loop()
                    # upload_datas = loop.create_task(requests.put(upload_session['uploadUrl'], data=chunk_data, headers=headers2))
                    # await asyncio.wait_for(upload_datas, timeout=3300)
                    # 上传
                    # chunk_data_upload = grequests.put(upload_session['uploadUrl'], data=chunk_data, headers=headers2)
                    # grequests.map(chunk_data_upload)
                    # chunk_data_upload = requests.put(upload_session['uploadUrl'], data=chunk_data, headers=headers2)

                    # 协程异步请求 阻塞会自动切换
                    future = asyncio.get_event_loop().run_in_executor(None, functools.partial(requests.put, upload_session['uploadUrl'], data=chunk_data, headers=headers2))

                    chunk_data_upload = await future
                    i = i + 1
                    if i == (chunk_number + 1):
                        s = chunk_data_upload.json()
                        # print(s)
                        # print(s)
                        # 正则表达式提取文件ID
                        file_id = re.findall('(\w{8}-\w{4}-\w{4}-\w{4}-\w{12})', s['eTag'])
                        url = await getUrl(headers, file_id[0])
                        # print(file_name + "---" + url)
                        file_data.close()
                        return_data['url'] = url
                        return return_data
        except Exception as e:
            print('发生错误.........')
            print(e)
            return ''




async def set_onedrive(path,name,type):
    # 应用程序(客户端) ID
    CLIENT_ID = '9ff21b1a-8908-4159-9e4b-17a0746855d7'
    # 目录(租户) ID
    TENANT_ID = '5d444e55-0cb2-4e42-bb34-fc0c3814c76c'
    # 账号
    USERNAME = 'test@wynb.onmicrosoft.com'
    # 密码
    PASSWORD = '150530Wang'

    # 获取access_token
    headers = await getToken(CLIENT_ID, TENANT_ID, USERNAME, PASSWORD)

    # 上传
    return await upload(headers, path,name,type)


# if __name__ == '__main__':
#     # 应用程序(客户端) ID
#     CLIENT_ID = '9ff21b1a-8908-4159-9e4b-17a0746855d7'
#     # 目录(租户) ID
#     TENANT_ID = '5d444e55-0cb2-4e42-bb34-fc0c3814c76c'
#     # 账号
#     USERNAME = 'test@wynb.onmicrosoft.com'
#     # 密码
#     PASSWORD = '150530Wang'
#
#     path = r"C:\Users\20696\Pictures\mp4"
#
#     # 获取access_token
#     headers = getToken(CLIENT_ID, TENANT_ID, USERNAME, PASSWORD)
#
#     # 上传
#     upload(headers, path)
