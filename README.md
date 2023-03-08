# OneDriveShareLinkPushAria2

从OneDrive或SharePoint共享链接提取下载URL并将其推送到aria2，即使在无图形界面的系统中依然可以使用。

## 依赖
requests==2.25.1

pyppeteer==0.2.5

## 特点
目前本程序支持的下载方式：
* xxx-my.sharepoint.com 下载链接的下载
  * 无下载密码的多文件推送
  * 有下载密码的多文件推送
  * 嵌套文件夹的文件推送
  * 任意选择文件推送
  * 针对超多文件（超过30个）的分享链接，实现了的遍历查看和下载
* xxx.sharepoint.com 下载链接的下载
* xxx-my.sharepoint.cn 下载链接的下载(理论上支持)

**注意：Aria2本身不支持HTTP POST型的下载链接，而OneDrive文件夹打包下载为HTTP POST型的下载链接，所以本程序将不会支持OneDrive文件夹打包下载**

## 使用说明
```bash
python main.py --help
usage: main.py [-h] [-d DOWNLOAD] [-f FILELIST] url

positional arguments:
  url                   分享链接

options:
  -h, --help            show this help message and exit
  -d DOWNLOAD, --download DOWNLOAD
                        是否下载
  -f FILELIST, --filelist FILELIST
                        文件列表
```
### 参数说明
* -d, --download: 是否下载文件，默认为`True`；如果为`False`，则只输出文件列表
* -f, --filelist: 要下载的文件列表，默认为**0**，表示下载所有文件

  如果想要下载第二个文件，则需要`-f 2`

  如果想要下载第二、第三个文件，则需要`-f 2-3`

  如果想要下载第二、第三、第四、第七个文件，则需要`-f 2-4,7`

  以此类推。


[main.py](../main.py) 中还定义了一些配置参数：
* `aria2_link: aria2` 的rpc地址，如果是本机，一般是 `http://localhost:端口号/jsonrpc`
* `aria2_secret`: aria2 的密码

## 输出文件列表

使用以下命令输出文件列表到list.txt

``` bash
python main.py [url] -d False > list.txt
```

使用powershell运行此命令可能会输出乱码, 先运行以下命令即可修复

``` bash
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

## 无密码的链接

```
python main.py url
```

确保目标aria2处于开启状态，执行

<!-- ## 有密码的链接

此时需要使用有密码的下载代码，也就是[havepassword.py](../havepassword.py)，打开这个文件，可以看到有一些全局变量（重复的不再赘述）：
* OneDriveSharePwd: OneDrive链接的密码
  
使用方法和上面类似。

# 注意
使用前，使用 `git clone https://github.com/dslwind/OneDriveShareLinkPushAria2.git` 将项目整个克隆，才能使用，`havepassword.py`依赖于`main.py`，如果要使用需要密码的版本，需要 `pip install pyppeteer` -->