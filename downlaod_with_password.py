import argparse
import asyncio
import os

from pyppeteer import launch

from download import download_files, get_files, header, wildcards_match_files

aria2_link = "http://localhost:6800/jsonrpc"
aria2_secret = ""

os.environ['PYPPETEER_HOME'] = os.path.split(os.path.realpath(__file__))[0]
# os.environ['PYPPETEER_DOWNLOAD_HOST'] = "http://npm.taobao.org/mirrors"

pheader = {}
url = ""


async def main(iurl, password):
    global pheader, url
    browser = await launch(options={'args': ['--no-sandbox']})
    page = await browser.newPage()
    await page.goto(iurl, {'waitUntil': 'networkidle0'})
    await page.focus("input[id='txtPassword']")
    await page.keyboard.type(password)
    verity_elem = await page.querySelector("input[id='btnSubmitPassword']")
    print("密码输入完成，正在跳转")

    await asyncio.gather(
        page.waitForNavigation(),
        verity_elem.click(),
    )
    url = await page.evaluate('window.location.href', force_expr=True)
    await page.screenshot({'path': 'example.png'})
    print("正在获取Cookie")
    # print(p.headers, p.url)
    _cookie = await page.cookies()
    pheader = ""
    for __cookie in _cookie:
        coo = "{}={};".format(__cookie.get("name"), __cookie.get("value"))
        pheader += coo
    await browser.close()


def get_files_with_password(iurl, password):
    global header
    print("正在启动无头浏览器模拟输入密码")
    asyncio.get_event_loop().run_until_complete(main(iurl, password))
    print("无头浏览器关闭，正在获取文件列表")
    print()
    header['cookie'] = pheader
    print(get_files(url, None, 0))


def download_files_with_password(iurl, password, aria2_url, token, num=-1):
    global header
    print("正在启动无头浏览器模拟输入密码")
    asyncio.get_event_loop().run_until_complete(main(iurl, password))
    print("无头浏览器关闭，正在获取文件列表")
    header['cookie'] = pheader
    download_files(url, None, 0, aria2_url, token, num=num)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='分享链接')
    parser.add_argument('-d', '--download', default=True, help='是否下载')
    parser.add_argument('-f', '--filelist', default="0", help='文件列表')
    parser.add_argument('-p', '--password', help='密码')
    args = parser.parse_args()

    aria2_link = "http://localhost:6800/jsonrpc"
    aria2_secret = ""

    # print(args.download == True)

    if args.download == True:
        download_files_with_password(args.url,
                                     args.password,
                                     aria2_link,
                                     aria2_secret,
                                     num=wildcards_match_files(args.filelist))
    elif str(args.download).lower() == 'false':
        get_files_with_password(args.url, args.password)
