# -*- coding: UTF-8 -*-
import re
import requests
import os
import sys
import time
from contextlib import closing
import hashlib
import json

#=============先修改
headers = {
    'User-agent': '__'}
cookies = {
    'ngaPassportUid': '__',
    'ngaPassportCid': '__',
}
#=============先修改
totalfloor = []  # int几层，str时间，str昵称，str内容，int赞数
tid = 0
title = 'title'
localmaxpage = 1
localmaxfloor = -1


def single(page):
    print('trypage%d' % page)
    params = (
        ('tid', tid),
        ('page', page),
        ('lite', 'js')
    )
    ss1 = requests.Session()
    get = ss1.get('https://bbs.nga.cn/read.php', headers=headers,
                  params=params, cookies=cookies)
    get.encoding = 'GBK'
    content = get.text.replace('	', '')  # 过滤掉防止json解析出错

    usertext = re.search(r',"__U":(.+?),"__R":', content, flags=re.S).group(1)
    userdict = json.loads(usertext)

    replytext = re.search(r',"__R":(.+?),"__T":', content, flags=re.S).group(1)
    replydict = json.loads(replytext)

    ttext = re.search(r',"__T":(.+?),"__F":', content, flags=re.S).group(1)
    tdict = json.loads(ttext)

    global title
    title = tdict['subject']

    for i in range(len(replydict)):
        totalfloor.append([int(replydict[str(i)]['lou']), replydict[str(i)]['postdate'], userdict[str(
            replydict[str(i)]['authorid'])]['username'], replydict[str(i)]['content'], int(replydict[str(i)]['score'])])

    return tdict['lastposter'] != totalfloor[len(totalfloor)-1][2]


def makefile():
    global localmaxfloor
    lastfloor = 0
    with open(('./%d/post.md' % tid), 'a', encoding='utf-8') as f:
        for onefloor in totalfloor:
            if localmaxfloor < int(onefloor[0]):
                if onefloor[0] == 0:
                    f.write('### %s\n\n' % title)

                f.write("----\n##### %d.[%d] %s by %s\n" %
                        (onefloor[0], onefloor[4], onefloor[1], onefloor[2]))
                raw = str(onefloor[3])

                raw = raw.replace('<br/>', '\n')  # 换行
                raw = raw.replace('<br>', '\n')

                rex = re.findall(r'(?<=\[img\]).+?(?=\[/img\])', raw)  # 图片
                for ritem in rex:
                    url = str(ritem)
                    if url[0:2] == './':
                        url = 'https://img.nga.178.com/attachments/' + url[2:]
                    url = url.replace('.medium.jpg', '')
                    filename = hashlib.md5(
                        bytes(url, encoding='utf-8')).hexdigest()[2:8] + url[-6:]
                    if os.path.exists('./%d/%s' % (tid, filename)) == False:
                        down(url, ('./%d/%s' % (tid, filename)))
                        print('down:%s' % ('./%d/%s' % (tid, filename)))
                    raw = raw.replace(('[img]%s[/img]' %
                                       ritem), ('![img](./%s)' % filename))

                rex = re.findall(r'\[s\:(a2|ac)\:(.+?)\]', raw)  # 表情
                for ritem in rex:
                    raw = raw.replace('[s:%s:%s]' % (
                        ritem[0], ritem[1]), '![%s](../smile/%s.png)' % (ritem[0]+ritem[1], ritem[0]+ritem[1]))
                #[0]人名 [1]时间 [2]圈的内容
                # 引用 [quote][tid=0000000]Topic[/tid] [b]Post by [uid=000000]whowhowho[/uid] (2020-03-26 01:07):[/b]
                rex = re.findall(
                    r'\[quote\].+?\[uid=\d+\](.+?)\[/uid\] \((.+?)\)\:\[/b\](.+?)\[/quote\]', raw, flags=re.S)
                for ritem in rex:
                    quotetext = ritem[2]
                    quotetext = quotetext.replace('\n', '\n>')
                    raw = raw.replace(re.search(r'\[quote\].+?\[uid=\d+\](.+?)\[/uid\] \((.+?)\)\:\[/b\](.+?)\[/quote\]',
                                                raw, flags=re.S).group(), '>%s(%s) said:%s' % (ritem[0], ritem[1], quotetext))

                f.write(("%s\n\n" % raw))
                lastfloor = int(onefloor[0])
    return lastfloor


def down(url, path):
    with closing(requests.get(url, stream=True)) as response:
        chunk_size = 1024  # 单次请求最大值
        with open(path, "wb") as file:
            for data in response.iter_content(chunk_size=chunk_size):
                file.write(data)


def main():
    global tid
    tid = int(input('tid:'))
    holder()
    input('press to exit.')


def holder():
    global localmaxpage
    global localmaxfloor
    print(tid)
    if not os.path.exists(('./%d' % tid)):
        os.mkdir(('./%d' % tid))
    elif os.path.exists('./%d/max.txt' % tid):
        with open('./%d/max.txt' % tid, 'r', encoding='utf-8') as f:
            r = f.read()
            localmaxpage = int(r.split()[0])
            localmaxfloor = int(r.split()[1])

    print('localmaxpage%d\nlocalmaxfloor%d' % (localmaxpage, localmaxfloor))
    cpage = localmaxpage
    while single(cpage) != False:
        cpage = cpage + 1

    with open(('./%d/max.txt' % tid), 'w', encoding='utf-8') as f:
        f.write("%d %s" % (cpage, totalfloor[len(totalfloor) - 1][0]))

    if os.path.exists('./%d/info.txt' % tid):
        with open(('./%d/info.txt' % tid), 'a', encoding='utf-8') as f:
            f.write('[%s]%d\n' % (time.asctime(
                time.localtime(time.time())), len(totalfloor)))
    else:
        with open(('./%d/info.txt' % tid), 'w', encoding='utf-8') as f:
            f.write('tid:%d\ntitle:%s\n' % (tid, title))
            f.write(
                ('[%s]%d\n' % (time.asctime(time.localtime(time.time())), len(totalfloor))))

    print('makeuntil:%d' % makefile())


if __name__ == '__main__':
    main()
