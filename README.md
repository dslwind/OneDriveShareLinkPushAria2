# OneDriveShareLinkPushAria2

从OneDrive或SharePoint共享链接提取下载URL并将其推送到aria2，即使在无图形界面的系统中依然可以使用。

## 依赖
```
requests
pyppeteer
```
需要安装aria2，并保持开启状态。Windows下可以使用Motrix，Linux系统安装配置参考[Aria2 一键安装管理脚本 增强版](https://github.com/P3TERX/aria2.sh)。

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
usage: main.py [-h] [-d DOWNLOAD] [-f FILELIST] [-p PASSWORD] url

positional arguments:
  url                   分享链接

options:
  -h, --help            show this help message and exit
  -d DOWNLOAD, --download DOWNLOAD
                        是否下载
  -f FILELIST, --filelist FILELIST
                        文件列表
  -p PASSWORD, --password PASSWORD
                        密码                        
```
### 参数说明
* -d, --download: 是否下载文件，默认为`True`；如果为`False`，则只输出文件列表
* -p, --password：分享链接的密码，仅适用于带密码的链接，默认为空
* -f, --filelist: 要下载的文件列表，默认为**0**，表示下载所有文件
  * 如果想要下载第二个文件，则需要`-f 2`

  * 如果想要下载第二、第三个文件，则需要`-f 2-3`

  * 如果想要下载第二、第三、第四、第七个文件，则需要`-f 2-4,7`

  以此类推。

[main.py](main.py) 中还定义了一些配置参数：
* `aria2_link: aria2` 的rpc地址，如果是本机，一般是 `http://localhost:端口号/jsonrpc`
* `aria2_secret`: aria2 的密码，默认为空

## 输出文件列表

使用以下命令输出文件列表到list.txt

``` bash
python main.py [url] -d False > list.txt
```

使用powershell运行此命令可能会输出乱码, 先运行以下命令即可修复

``` bash
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```