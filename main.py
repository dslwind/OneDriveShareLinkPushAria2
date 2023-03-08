import argparse
import copy
import io
import json
import os
import re
import sys
import urllib
import urllib.request
from pprint import pprint
from urllib import parse

import requests
from requests.adapters import HTTPAdapter, Retry

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
file_count = 0

header = {
    'sec-ch-ua-mobile': '?0',
    'upgrade-insecure-requests': '1',
    'dnt': '1',
    'user-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.51',
    'accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'service-worker-navigation-preload': 'true',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-dest': 'iframe',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}


def new_session():
    s = requests.session()
    retries = Retry(total=5, backoff_factor=0.1)
    s.mount('http://', HTTPAdapter(max_retries=retries))
    return s


def get_files(original_path, req, layers, _id=0):
    global file_count
    # new_url = urllib.parse.urlparse(originalPath)
    # header["host"] = new_url.netloc
    # print(header)
    is_sharepoint = False
    if "-my" not in original_path:
        is_sharepoint = True
    if req == None:
        req = new_session()
    reqf = req.get(original_path, headers=header)
    # f = open("a.html", "w+", encoding="utf-8")
    # f.write(reqf.text)
    # f.close()
    if ',"FirstRow"' not in reqf.text:
        print("\t" * layers, "这个文件夹没有文件")
        return 0

    files_data = []

    # print(p.group(1))
    redirect_url = reqf.url

    query = dict(
        urllib.parse.parse_qsl(urllib.parse.urlsplit(redirect_url).query))
    redirect_split_url = redirect_url.split("/")

    relative_folder = ""
    root_folder = query["id"]
    for i in root_folder.split("/"):
        if is_sharepoint:
            if i != "Shared Documents":
                relative_folder += i + "/"
            else:
                relative_folder += i
                break
        else:
            if i != "Documents":
                relative_folder += i + "/"
            else:
                relative_folder += i
                break
    relative_url = parse.quote(relative_folder).replace("/", "%2F").replace(
        "_", "%5F").replace("-", "%2D")
    root_folder_url = parse.quote(root_folder).replace("/", "%2F").replace(
        "_", "%5F").replace("-", "%2D")

    graphql_var = '{"query":"query (\n        $listServerRelativeUrl: String!,$renderListDataAsStreamParameters: RenderListDataAsStreamParameters!,$renderListDataAsStreamQueryString: String!\n        )\n      {\n      \n      legacy {\n      \n      renderListDataAsStream(\n      listServerRelativeUrl: $listServerRelativeUrl,\n      parameters: $renderListDataAsStreamParameters,\n      queryString: $renderListDataAsStreamQueryString\n      )\n    }\n      \n      \n  perf {\n    executionTime\n    overheadTime\n    parsingTime\n    queryCount\n    validationTime\n    resolvers {\n      name\n      queryCount\n      resolveTime\n      waitTime\n    }\n  }\n    }","variables":{"listServerRelativeUrl":"%s","renderListDataAsStreamParameters":{"renderOptions":5707527,"allowMultipleValueFilterForTaxonomyFields":true,"addRequiredFields":true,"folderServerRelativeUrl":"%s"},"renderListDataAsStreamQueryString":"@a1=\'%s\'&RootFolder=%s&TryNewExperienceSingle=TRUE"}}' % (
        relative_folder, root_folder, relative_url, root_folder_url)

    # print(graphqlVar)
    s2 = urllib.parse.urlparse(redirect_url)
    temp_header = copy.deepcopy(header)
    temp_header["referer"] = redirect_url
    temp_header["cookie"] = reqf.headers["set-cookie"]
    temp_header["authority"] = s2.netloc
    temp_header["content-type"] = "application/json;odata=verbose"
    # print(redirectSplitURL)

    graphql_req = req.post("/".join(redirect_split_url[:-3]) +
                           "/_api/v2.1/graphql",
                           data=graphql_var.encode('utf-8'),
                           headers=temp_header)
    graphql_req = json.loads(graphql_req.text)
    # print(graphqlReq)
    if "NextHref" in graphql_req["data"]["legacy"]["renderListDataAsStream"][
            "ListData"]:
        next_href = graphql_req["data"]["legacy"]["renderListDataAsStream"][
            "ListData"]["NextHref"] + "&@a1=%s&TryNewExperienceSingle=TRUE" % (
                "%27" + relative_url + "%27")
        files_data.extend(graphql_req["data"]["legacy"]
                          ["renderListDataAsStream"]["ListData"]["Row"])
        # print(filesData)

        list_view_xml = graphql_req["data"]["legacy"][
            "renderListDataAsStream"]["ViewMetadata"]["ListViewXml"]
        render_list_data_as_stream_var = '{"parameters":{"__metadata":{"type":"SP.RenderListDataParameters"},"RenderOptions":1216519,"ViewXml":"%s","AllowMultipleValueFilterForTaxonomyFields":true,"AddRequiredFields":true}}' % list_view_xml.replace(
            '"', '\\"')
        # print(renderListDataAsStreamVar, nextHref,1)

        # print(listViewXml)

        graphql_req = req.post(
            "/".join(redirect_split_url[:-3]) +
            "/_api/web/GetListUsingPath(DecodedUrl=@a1)/RenderListDataAsStream"
            + next_href,
            data=render_list_data_as_stream_var.encode('utf-8'),
            headers=temp_header)
        graphql_req = json.loads(graphql_req.text)
        # print(graphqlReq)

        while "NextHref" in graphql_req["ListData"]:
            next_href = graphql_req["ListData"][
                "NextHref"] + "&@a1=%s&TryNewExperienceSingle=TRUE" % (
                    "%27" + relative_url + "%27")
            files_data.extend(graphql_req["ListData"]["Row"])
            graphql_req = req.post(
                "/".join(redirect_split_url[:-3]) +
                "/_api/web/GetListUsingPath(DecodedUrl=@a1)/RenderListDataAsStream"
                + next_href,
                data=render_list_data_as_stream_var.encode('utf-8'),
                headers=temp_header)
            # print(graphqlReq.text)
            graphql_req = json.loads(graphql_req.text)
            # print(graphqlReq)
        files_data.extend(graphql_req["ListData"]["Row"])
    else:
        files_data.extend(graphql_req["data"]["legacy"]
                          ["renderListDataAsStream"]["ListData"]["Row"])
    # fileCount = 0
    # 不重置文件计数
    for i in files_data:
        if i['FSObjType'] == "1":
            print("\t" * layers, "文件夹：", i['FileLeafRef'], "\tUUID：",
                  i["UniqueId"])
            _query = query.copy()
            _query['id'] = os.path.join(_query['id'],
                                        i['FileLeafRef']).replace("\\", "/")
            if not is_sharepoint:
                original_path = "/".join(redirect_split_url[:-1]) + \
                    "/onedrive.aspx?" + urllib.parse.urlencode(_query)
            else:
                original_path = "/".join(redirect_split_url[:-1]) + \
                    "/AllItems.aspx?" + urllib.parse.urlencode(_query)
            get_files(original_path, req, layers + 1, _id=file_count)
            # fileCount += getFiles(originalPath, req, layers+1, _id=fileCount)
        else:
            file_count += 1
            print(
                "\t" * layers, "文件 [%d]：%s\tUUID：%s" %
                (file_count, i['FileLeafRef'], i["UniqueId"]))
    return file_count


def download_files(original_path,
                   req,
                   layers,
                   aria2_url,
                   token,
                   num=[0],
                   _id=0,
                   original_dir=""):
    global file_count
    if req == None:
        req = new_session()
    # print(header)
    if original_dir == "":
        original_dir = get_aria2_config_dir(aria2_url, token)
    reqf = req.get(original_path, headers=header)
    is_sharepoint = False
    if "-my" not in original_path:
        is_sharepoint = True

    # f=open()
    if ',"FirstRow"' not in reqf.text:
        print("\t" * layers, "这个文件夹没有文件")
        return 0

    files_data = []
    redirect_url = reqf.url
    redirect_split_url = redirect_url.split("/")
    query = dict(
        urllib.parse.parse_qsl(urllib.parse.urlsplit(redirect_url).query))
    download_url = "/".join(
        redirect_split_url[:-1]) + "/download.aspx?UniqueId="
    if is_sharepoint:
        pat = re.search('templateUrl":"(.*?)"', reqf.text)

        download_url = pat.group(1)
        download_url = urllib.parse.urlparse(download_url)
        download_url = "{}://{}{}".format(download_url.scheme,
                                          download_url.netloc,
                                          download_url.path).split("/")
        download_url = "/".join(download_url[:-1]) + \
            "/download.aspx?UniqueId="
        # print(downloadURL)

    # print(reqf.headers)

    s2 = urllib.parse.urlparse(redirect_url)
    header["referer"] = redirect_url
    header["cookie"] = reqf.headers["set-cookie"]
    header["authority"] = s2.netloc

    # .replace("-", "%2D")

    # print(dd, [cc])
    header_str = ""
    for key, value in header.items():
        # print(key+':'+str(value))
        header_str += key + ':' + str(value) + "\n"

    relative_folder = ""
    root_folder = query["id"]
    for i in root_folder.split("/"):
        if is_sharepoint:
            if i != "Shared Documents":
                relative_folder += i + "/"
            else:
                relative_folder += i
                break
        else:
            if i != "Documents":
                relative_folder += i + "/"
            else:
                relative_folder += i
                break
    relative_url = parse.quote(relative_folder).replace("/", "%2F").replace(
        "_", "%5F").replace("-", "%2D")
    root_folder_url = parse.quote(root_folder).replace("/", "%2F").replace(
        "_", "%5F").replace("-", "%2D")

    graphql_var = '{"query":"query (\n        $listServerRelativeUrl: String!,$renderListDataAsStreamParameters: RenderListDataAsStreamParameters!,$renderListDataAsStreamQueryString: String!\n        )\n      {\n      \n      legacy {\n      \n      renderListDataAsStream(\n      listServerRelativeUrl: $listServerRelativeUrl,\n      parameters: $renderListDataAsStreamParameters,\n      queryString: $renderListDataAsStreamQueryString\n      )\n    }\n      \n      \n  perf {\n    executionTime\n    overheadTime\n    parsingTime\n    queryCount\n    validationTime\n    resolvers {\n      name\n      queryCount\n      resolveTime\n      waitTime\n    }\n  }\n    }","variables":{"listServerRelativeUrl":"%s","renderListDataAsStreamParameters":{"renderOptions":5707527,"allowMultipleValueFilterForTaxonomyFields":true,"addRequiredFields":true,"folderServerRelativeUrl":"%s"},"renderListDataAsStreamQueryString":"@a1=\'%s\'&RootFolder=%s&TryNewExperienceSingle=TRUE"}}' % (
        relative_folder, root_folder, relative_url, root_folder_url)

    # print(graphqlVar)
    s2 = urllib.parse.urlparse(redirect_url)
    temp_header = copy.deepcopy(header)
    temp_header["referer"] = redirect_url
    temp_header["cookie"] = reqf.headers["set-cookie"]
    temp_header["authority"] = s2.netloc
    temp_header["content-type"] = "application/json;odata=verbose"
    # print(redirectSplitURL)

    graphql_req = req.post("/".join(redirect_split_url[:-3]) +
                           "/_api/v2.1/graphql",
                           data=graphql_var.encode('utf-8'),
                           headers=temp_header)
    graphql_req = json.loads(graphql_req.text)
    # print(graphqlReq)
    if "NextHref" in graphql_req["data"]["legacy"]["renderListDataAsStream"][
            "ListData"]:
        next_href = graphql_req["data"]["legacy"]["renderListDataAsStream"][
            "ListData"]["NextHref"] + "&@a1=%s&TryNewExperienceSingle=TRUE" % (
                "%27" + relative_url + "%27")
        files_data.extend(graphql_req["data"]["legacy"]
                          ["renderListDataAsStream"]["ListData"]["Row"])
        # print(filesData)

        list_view_xml = graphql_req["data"]["legacy"][
            "renderListDataAsStream"]["ViewMetadata"]["ListViewXml"]
        render_list_data_as_stream_var = '{"parameters":{"__metadata":{"type":"SP.RenderListDataParameters"},"RenderOptions":1216519,"ViewXml":"%s","AllowMultipleValueFilterForTaxonomyFields":true,"AddRequiredFields":true}}' % list_view_xml.replace(
            '"', '\\"')
        # print(renderListDataAsStreamVar, nextHref,1)

        # print(listViewXml)

        graphql_req = req.post(
            "/".join(redirect_split_url[:-3]) +
            "/_api/web/GetListUsingPath(DecodedUrl=@a1)/RenderListDataAsStream"
            + next_href,
            data=render_list_data_as_stream_var.encode('utf-8'),
            headers=temp_header)
        graphql_req = json.loads(graphql_req.text)
        # print(graphqlReq)

        while "NextHref" in graphql_req["ListData"]:
            next_href = graphql_req["ListData"][
                "NextHref"] + "&@a1=%s&TryNewExperienceSingle=TRUE" % (
                    "%27" + relative_url + "%27")
            files_data.extend(graphql_req["ListData"]["Row"])
            graphql_req = req.post(
                "/".join(redirect_split_url[:-3]) +
                "/_api/web/GetListUsingPath(DecodedUrl=@a1)/RenderListDataAsStream"
                + next_href,
                data=render_list_data_as_stream_var.encode('utf-8'),
                headers=temp_header)
            # print(graphqlReq.text)
            graphql_req = json.loads(graphql_req.text)
            # print(graphqlReq)
        files_data.extend(graphql_req["ListData"]["Row"])
    else:
        files_data.extend(graphql_req["data"]["legacy"]
                          ["renderListDataAsStream"]["ListData"]["Row"])

    # fileCount = 0
    for i in files_data:
        if i['FSObjType'] == "1":
            print("\t" * layers, "文件夹：", i['FileLeafRef'], "\tUUID：",
                  i["UniqueId"], "正在进入")
            _query = query.copy()
            _query['id'] = os.path.join(_query['id'],
                                        i['FileLeafRef']).replace("\\", "/")
            if not is_sharepoint:
                original_path = "/".join(redirect_split_url[:-1]) + \
                    "/onedrive.aspx?" + urllib.parse.urlencode(_query)
            else:
                original_path = "/".join(redirect_split_url[:-1]) + \
                    "/AllItems.aspx?" + urllib.parse.urlencode(_query)
            download_files(original_path,
                           req,
                           layers + 1,
                           aria2_url,
                           token,
                           num=num,
                           _id=file_count,
                           original_dir=original_dir)
            # fileCount += downloadFiles(originalPath, req, layers+1,
            #                            aria2URL, token, num=num, _id=fileCount, originalDir=originalDir)
        else:
            file_count += 1
            # print(num)
            if num == [0] or (isinstance(num, list) and file_count in num):
                print(
                    "\t" * layers, "文件 [%d]：%s\tUUID：%s\t正在推送" %
                    (file_count, i['FileLeafRef'], i["UniqueId"]))
                cc = download_url + (i["UniqueId"][1:-1].lower())
                dd = dict(out=i["FileLeafRef"],
                          header=header_str,
                          dir=original_dir +
                          str(query['id']).split('Documents', 1)[1])
                jsonreq = json.dumps({
                    'jsonrpc': '2.0',
                    'id': 'qwer',
                    'method': 'aria2.addUri',
                    "params": ["token:" + token, [cc], dd]
                })

                c = requests.post(aria2_url, data=jsonreq)
                pprint(json.loads(c.text))
                # exit(0)
            else:
                print(
                    "\t" * layers, "文件 [%d]：%s\tUUID：%s\t非目标文件" %
                    (file_count, i['FileLeafRef'], i["UniqueId"]))
    return file_count


def get_files_have_pwd(original_path, password):
    req = new_session()
    req.cookies.update(header)
    r = req.get(original_path)
    p = re.search('SideBySideToken" value="(.*?)" />', r.text)
    side_by_side_token = p.group(1)
    p = re.search('id="__VIEWSTATE" value="(.*?)" />', r.text)
    __VIEWSTATE = p.group(1)
    p = re.search('id="__VIEWSTATEGENERATOR" value="(.*?)" />', r.text)
    __VIEWSTATEGENERATOR = p.group(1)
    p = re.search('__EVENTVALIDATION" value="(.*?)" />', r.text)
    __EVENTVALIDATION = p.group(1)
    s2 = parse.urlparse(original_path)
    redirect_url = original_path
    redirect_split_url = redirect_url.split("/")
    share_query = s2.path.split("/")[-1]
    redirect_split_url[
        -1] = "guestaccess.aspx?" + s2.query + "&share=" + share_query
    pwd_url = "/".join(redirect_split_url)
    print(pwd_url, r.headers)
    hew_header = {
        'sec-ch-ua-mobile': '?0',
        'upgrade-insecure-requests': '1',
        'dnt': '1',
        'user-agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36 Edg/90.0.818.51',
        'accept':
        'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'content-type': 'application/x-www-form-urlencoded',
        "connection": "keep-alive",
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        "host": s2.netloc,
        "origin": s2.scheme + "://" + s2.netloc,
        "Referer": original_path,
        'sec-ch-ua-mobile': '?0',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
    }

    req.cookies.update(header)
    r = req.post(pwd_url,
                 data={
                     "__EVENTTARGET": "btnSubmitPassword",
                     "__EVENTARGUMENT": None,
                     "SideBySideToken": side_by_side_token,
                     "__VIEWSTATE": __VIEWSTATE,
                     "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
                     "__VIEWSTATEENCRYPTED": None,
                     "__EVENTVALIDATION": __EVENTVALIDATION,
                     "txtPassword": password
                 },
                 headers=hew_header,
                 allow_redirects=False)
    print(r.headers, r.text)
    new_url = r.headers["Location"]

    r = req.get(new_url, headers=r.headers, allow_redirects=False)
    print(r.headers, r.text)


def wildcards_match_files(text):
    file_list = []
    data = text.split(",")
    for v in data:
        i = v.split("-")
        if len(i) < 2:
            file_list.append(int(i[0]))
        else:
            for j in range(int(i[0]), int(i[1]) + 1):
                file_list.append(j)
    # print(fileNum)
    file_list = list(set(file_list))
    return sorted(file_list)


def get_aria2_config_dir(aria2_url, token):
    jsonreq = json.dumps({
        'jsonrpc': '2.0',
        'id': 'qwer',
        'method': 'aria2.getGlobalOption',
        "params": ["token:" + token]
    })
    c = requests.post(aria2_url, data=jsonreq)
    return json.loads(c.text)["result"]["dir"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='分享链接')
    parser.add_argument('-d', '--download', default=True, help='是否下载')
    parser.add_argument('-f', '--filelist', default="0", help='文件列表')
    args = parser.parse_args()

    aria2_link = "http://localhost:16800/jsonrpc"
    aria2_secret = ""

    # print(args.download == True)

    if args.download == True:
        download_files(args.url,
                       None,
                       0,
                       aria2_link,
                       aria2_secret,
                       num=wildcards_match_files(args.filelist))
    elif str(args.download).lower() == 'false':
        get_files(args.url, None, 0)


if __name__ == "__main__":
    main()