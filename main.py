import argparse
import io
import sys

from utils import (download_files, download_files_with_password, get_files,
                   get_files_with_password, wildcards_match_files)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='分享链接')
    parser.add_argument('-d', '--download', default=True, help='是否下载')
    parser.add_argument('-f', '--filelist', default="0", help='文件列表')
    parser.add_argument('-p', '--password', default=None, help='密码')
    args = parser.parse_args()

    aria2_link = "http://localhost:6800/jsonrpc"
    aria2_secret = ""

    if args.password == None:
        if args.download == True:
            download_files(args.url,
                           None,
                           0,
                           aria2_link,
                           aria2_secret,
                           num=wildcards_match_files(args.filelist))
        elif str(args.download).lower() == 'false':
            get_files(args.url, None, 0)

    else:
        if args.download == True:
            download_files_with_password(args.url,
                                         args.password,
                                         aria2_link,
                                         aria2_secret,
                                         num=wildcards_match_files(
                                             args.filelist))
        elif str(args.download).lower() == 'false':
            get_files_with_password(args.url, args.password)


if __name__ == "__main__":
    main()