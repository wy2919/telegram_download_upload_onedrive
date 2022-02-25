# telegram_download_upload_onedrive
telegram下载频道图片上传到onedrive


# 一键下载 开启

```
docker run -it --name py 150530/git_telegram_onedrive bash -c 'git clone https://github.com/wy2919/telegram_download_upload_onedrive.git &&  cd telegram_download_upload_onedrive/ &&   nohup python -u  telegram_download_1.py > /log.log '
```

```
docker run -it --name py 150530/git_telegram_onedrive bash -c 'git clone https://github.com/wy2919/telegram_download_upload_onedrive.git &&  cd telegram_download_upload_onedrive/ &&   nohup python -u  telegram_download_2.py > /log.log '
```

```
docker run -it --name py 150530/git_telegram_onedrive bash -c 'git clone https://github.com/wy2919/telegram_download_upload_onedrive.git &&  cd telegram_download_upload_onedrive/ &&   nohup python -u  telegram_download_3.py > /log.log '
```

# 进入容器查看日志

```
docker exec -it py bash -c ' tail -f log.log'
```
