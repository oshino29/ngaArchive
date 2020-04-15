# -*- coding: UTF-8 -*-
import re
import requests
import os
import sys
import time
from contextlib import closing
import hashlib

#=============先修改
headers = {
        'User-agent': '__'}
cookies = {
        'ngaPassportUid': '__',
        'bbsmisccookies': '__',
        'ngacn0comUserInfo': '__',
        'ngacn0comUserInfoCheck': '__',
        'ngacn0comInfoCheckTime': '__',
        'ngaPassportUrlencodedUname': '__',
        'ngaPassportCid': '__',
}
#=============先修改
totalfloor = []
tid = 0
title = 'title'
localmaxpage = 1
localmaxfloor = -1


def single(page):
    print ('trypage%d' % page)
    params = (
        ('tid', tid),
        ('_ff', '-7'),
        ('page', page)
    )
    ss1 = requests.Session()
    get = ss1.get('https://bbs.nga.cn/read.php', headers=headers,
                  params=params, cookies=cookies)
    get.encoding = 'GBK'
    content = get.text
    global title
    title = re.search(r'<title>(.+?)</title>', content, flags=re.S).group(1)
    userdict = {}
    rex = re.findall(r'"uid":(\d+?),"username":"(.+?)",', content, flags=re.S)
    for ritem in rex:
        userdict[ritem[0]] = ritem[1]
    
    reply = re.findall(r'func=ucp&uid=(\d+)\' id=\'postauthor.+?\'reply time\'>(.+?)</span></div>.+?<(?:p|span) id=\'postcontent(\d+?)\' class=\'postcontent ubbcode\'>(.+?)</(?:p|span)>', content, flags=re.S)
    for i in range(len(reply)):
        totalfloor.append([reply[i][2], reply[i][1], userdict[reply[i][0]], reply[i][3]])
    return re.search(r'下一页', content) != None

def makefile():
    global localmaxfloor
    lastfloor = 0
    with open(('./%d/post.md' % tid),'a',encoding='utf-8') as f:
        for onefloor in totalfloor:
            if localmaxfloor<int(onefloor[0]):
                
                f.write("----\n##### %s. %s by %s\n" % (onefloor[0], onefloor[1], onefloor[2]))
                raw = str(onefloor[3])

                raw = raw.replace('<br/>','\n')#换行
                raw = raw.replace('<br>','\n')

                rex = re.findall(r'(?<=\[img\]).+?(?=\[/img\])',raw)#图片
                for ritem in rex:
                    url = str(ritem)
                    if url[0:2] == './':
                        url = 'https://img.nga.178.com/attachments/' + url[2:]
                    url = url.replace('.medium.jpg','')
                    filename = hashlib.md5(bytes(url, encoding='utf-8')).hexdigest()[2:8] + url[-6:]
                    if os.path.exists('./%d/%s' % (tid,filename)) == False:
                        down(url,('./%d/%s' % (tid,filename)))
                        print('down:%s' % ('./%d/%s' % (tid,filename)))
                    raw = raw.replace(('[img]%s[/img]' % ritem),('![img](./%s)' % filename))

                rex = re.findall(r'\[s\:(a2|ac)\:(.+?)\]',raw)#表情
                for ritem in rex:
                    raw = raw.replace('[s:%s:%s]' % (ritem[0], ritem[1]),'![%s](../smile/%s.png)' % (ritem[0]+ritem[1],ritem[0]+ritem[1]))
                #[0]人名 [1]时间 [2]圈的内容
                rex = re.findall(r'\[quote\].+?\[uid=\d+\](.+?)\[/uid\] \((.+?)\)\:\[/b\](.+?)\[/quote\]',raw, flags=re.S)#引用 [quote][tid=0000000]Topic[/tid] [b]Post by [uid=000000]whowhowho[/uid] (2020-03-26 01:07):[/b]
                for ritem in rex:
                    quotetext = ritem[2]
                    quotetext = quotetext.replace('\n','\n>')
                    raw = raw.replace(re.search(r'\[quote\].+?\[uid=\d+\](.+?)\[/uid\] \((.+?)\)\:\[/b\](.+?)\[/quote\]',raw, flags=re.S).group(),'>%s(%s) said:%s' % (ritem[0],ritem[1],quotetext))
                
                
                f.write(("%s\n\n" % raw))
                lastfloor = int(onefloor[0])
    return lastfloor
    
def down(url,path):
    with closing(requests.get(url, stream=True)) as response:
        chunk_size = 1024 # 单次请求最大值
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
        with open('./%d/max.txt' % tid,'r',encoding='utf-8') as f:
            r = f.read()
            localmaxpage = int(r.split( )[0])
            localmaxfloor = int(r.split( )[1])
    
    print('localmaxpage%d\nlocalmaxfloor%d' % (localmaxpage,localmaxfloor))
    cpage = localmaxpage
    while single(cpage) != False:
        cpage = cpage + 1

    with open(('./%d/max.txt' % tid),'w',encoding='utf-8') as f:
        f.write("%d %s" % (cpage, totalfloor[len(totalfloor) - 1][0]))
    
    if os.path.exists('./%d/info.txt' % tid):
        with open(('./%d/info.txt' % tid),'a',encoding='utf-8') as f:
            f.write('[%s]%d\n' % (time.asctime(time.localtime(time.time())), len(totalfloor) - 1))
    else:
        with open(('./%d/info.txt' % tid),'w',encoding='utf-8') as f:
            f.write('tid:%d\n' % tid)
            f.write(('[%s]%d\n' % (time.asctime(time.localtime(time.time())), len(totalfloor) - 1)))
    
    print('makeuntil:%d' % makefile())

if __name__ == '__main__':
    main()