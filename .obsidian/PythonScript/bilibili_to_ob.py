# 本脚本无需在Obsidian中安装额外插件

# 导入必要的库，也是你需要安装
# 可在cmd中输入pip install xxx(xxx为库名，如requests)
import requests
import re
import json
from pprint import *
import subprocess
import os

# 以下为主体代码，如务必要，请勿自行修改
# 如果有报错，可以在B站给我留言，或者github上提交问题

# 读取cookies
cookie = open("700 功能性文件/cookies.md", 'r', encoding="utf-8").read()

headers = {
    'referer': 'https://space.bilibili.com',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
    'cookie': cookie
}

#替换特殊字符
def xreplace(string):
    return string.replace('/','-').replace('|','｜').replace(':','：')

#判断文件/文件夹是否存在与某个目录或其子目录下
def xexists(name):
    for root, dirs, files in os.walk("./100 B站视频"):
        for file in files:
            if file == name:
                return True
        for adir in dirs:
            if adir == name:
                return True
    return False

#如果目录不存在则创建目录
def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        os.makedirs(path)
    else:
        pass

def write_note(bvid,folder_path,path_two,path_three):
    s = requests.session()
    vid = json.loads(s.get('https://api.bilibili.com/x/web-interface/view?bvid='+bvid,headers=headers).text)
    if 'BV' not in url:
        with open('error.md', 'w', encoding="utf-8") as f:
            f.write('暂时不支持此类型连接，请不要用此脚本爬取B站番剧和电影等，或者用于其他网站')
    elif 'data' in vid and 'ugc_season' not in vid['data']:
        bvid = vid['data']['bvid']
        # title = vid['data']['title'].replace('：','-').replace('|','-').replace('【','(').replace('】',')').replace('！','').replace('/','-')
        title = re.sub('([^\u4e00-\u9fa5])', '', vid['data']['title']).replace('/','-')
        video_url = 'https://www.bilibili.com/video/{}'.format(bvid)
        line = '- [ ] [{}]({})\n'.format(title, video_url)
        # print(line)
        with open('{}/{}.md'.format(path_one, title), 'w', encoding="utf-8") as f:
            f.write('---\ntarget: tasks\nstatus: in progress\ntags: bilibili\n---\n')
            f.write('# 学习视频\n')
            f.write(line)
            f.write('# 笔记\n')
    else:
        ep = vid['data']['ugc_season']['sections'][0]['episodes']
        epname = vid['data']['ugc_season']['title']
        cover = vid['data']['ugc_season']['cover']
        path_two = '{}/{}'.format(path_one,epname)
        path_three = '{}/{}'.format(path_two,'笔记')
        mkdir(path_two) 
        mkdir(path_three)
        for i in ep:
            # title = i['title'].replace('：','-').replace('|','-').replace('【','(').replace('】',')').replace('！','').replace('/','-')
            title = re.sub('([^\u4e00-\u9fa5])', '', i['title']).replace('/','-')
            bvid = i['bvid']
            video_url = 'https://www.bilibili.com/video/{}'.format(bvid)
            with open('{}/{}.md'.format(path_three, title), 'w', encoding="utf-8") as f:
                f.write('# 学习视频\n')
                line = '[{}]({})\n'.format(title, video_url)
                f.write(line)
                f.write('# 笔记\n')       

        with open('{}/{}.md'.format(path_two,epname), 'a', encoding="utf-8") as f:
            # f.write('---\n')
            # f.write('banner: {}\n'.format(cover))
            f.write('---\ntarget: tasks\nstatus: in progress\ntags: bilibili\n---\n')
            f.write('# 学习清单\n')
            for i in ep:
                title = re.sub('([^\u4e00-\u9fa5])', '', i['title']).replace('/','-')
                f.write('- [ ] [[{}]]\n'.format(i['title']))

def bilibili_to_ob(path_one,url):
    # 创建笔记文件夹
    # path_one = '100 B站视频'
    mkdir(path_one)
    # 爬取同步收藏夹内容
    response = requests.get(url=url, headers=headers)
    json_data = json.loads(response.text)
    medias = json_data['data']['medias']
    for i in medias:  #遍历每一个视频(media)
        # 获取新的爬取链接
        bvid = i['bvid']
        new_url = 'https://api.bilibili.com/x/web-interface/view?bvid={}'.format(bvid)
        vid = json.loads(requests.get(url=new_url, headers=headers).text)
        if 'data' in vid and 'ugc_season' not in vid['data']:
            # pprint.pprint(vid)
            # title = vid['data']['title'].replace('：','-').replace('|','-').replace('【','(').replace('】',')').replace('！','').replace('/','-')
            title = xreplace(vid['data']['title'])
            pages = vid['data']['pages']
            if len(pages) == 1:  #单个视频
                video_url = 'https://www.bilibili.com/video/{}'.format(bvid)
                line = '- [ ] [{}]({})\n'.format(title, video_url)
                # 判断笔记是否已经存在
                note = os.path.exists('{}/{}.md'.format(path_one, title))
                if not note:
                    with open('{}/{}.md'.format(path_one, title), 'w', encoding="utf-8") as f:
                        f.write('---\ntarget: tasks\nstatus: in progress\ntags: bilibili\n---\n')
                        f.write('# 学习视频\n')
                        f.write(line)
                        f.write('# 笔记\n')
                        # print('{} 视频已同步！'.format(title))
            else:  #系列视频
                # 创建对应文件夹
                path_two = '{}/{}'.format(path_one,title)
                path_three = '{}/{}'.format(path_two,'笔记')
                # 判断文件夹是否已经存在
                folder = os.path.exists(path_two)
                if not folder:               
                    # 如果不存在，则创建新目录
                    os.makedirs(path_three)
                    for i in pages:
                        # page_name = i['part'].replace('：','-').replace('|','-').replace('【','(').replace('】',')').replace('！','').replace('/','-')
                        page_name = re.sub('([^\u4e00-\u9fa5])', '', i['part']).replace('/','-')
                        # bvid = bvid + '?p={}'.format(i['page'])
                        video_url = 'https://www.bilibili.com/video/{}?p={}'.format(bvid,i['page'])
                        with open('{}/{}.md'.format(path_three, page_name), 'w', encoding="utf-8") as f:
                            f.write('# 学习视频\n')
                            line = '[{}]({})\n'.format(page_name, video_url)
                            f.write(line)
                            f.write('# 笔记\n') 
                    # print('{} 视频已同步！'.format(epname))
                    with open('{}/{}.md'.format(path_two,title), 'a', encoding="utf-8") as f:
                        # f.write('---\n')
                        # f.write('banner: {}\n'.format(cover))
                        f.write('---\ntarget: tasks\nstatus: in progress\ntags: bilibili\n---\n')
                        f.write('# 学习清单\n')
                        for i in pages:
                            page_name = re.sub('([^\u4e00-\u9fa5])', '', i['part']).replace('/','-')
                            f.write('- [ ] [[{}]]\n'.format(page_name))

        elif 'data' in vid and 'ugc_season' in vid['data']:
            # pprint.pprint(vid)
            ep = vid['data']['ugc_season']['sections'][0]['episodes']
            epname = vid['data']['ugc_season']['title']
            cover = vid['data']['ugc_season']['cover']
            # 创建对应文件夹
            path_two = '{}/{}'.format(path_one,epname)
            path_three = '{}/{}'.format(path_two,'笔记')
            # 判断文件夹是否已经存在
            folder = os.path.exists(path_two)
            if not folder:
                # 如果不存在，则创建新目录
                os.makedirs(path_three)
                for i in ep:
                    # title = i['title'].replace('：','-').replace('|','-').replace('【','(').replace('】',')').replace('！','').replace('/','-')
                    title = re.sub('([^\u4e00-\u9fa5])', '', i['title'])
                    bvid = i['bvid']
                    video_url = 'https://www.bilibili.com/video/{}'.format(bvid)
                    with open('{}/{}.md'.format(path_three, title), 'w', encoding="utf-8") as f:
                        f.write('# 学习视频\n')
                        line = '[{}]({})\n'.format(title, video_url)
                        f.write(line)
                        f.write('# 笔记\n') 
                # print('{} 视频已同步！'.format(epname))   

                with open('{}/{}.md'.format(path_two,epname), 'a', encoding="utf-8") as f:
                    # f.write('---\n')
                    # f.write('banner: {}\n'.format(cover))
                    f.write('---\ntarget: tasks\nstatus: in progress\ntags: bilibili\n---\n')
                    f.write('# 学习清单\n')
                    for i in ep:
                        # title = i['title'].replace('：','-').replace('|','-').replace('【','(').replace('】',')').replace('！','').replace('/','-')
                        title = re.sub('([^\u4e00-\u9fa5])', '', i['title']).replace('/','-')
                        f.write('- [ ] [[{}]]\n'.format(title))

def get_id():
    # 获取mid
    url = 'https://api.bilibili.com/x/web-interface/nav'
    json_data = json.loads(requests.get(url=url, headers=headers).text)
    mid = json_data['data']['mid']
    # 获取
    url = 'https://api.bilibili.com/x/v3/fav/folder/created/list-all?up_mid={}&jsonp=jsonp'.format(mid)
    json_data = json.loads(requests.get(url=url, headers=headers).text)
    pprint(json_data)
    id_list = []
    title_list = []
    count_list = []

    favorites_list = json_data['data']['list']  #获取所有收藏夹的元数据
    f = {}
    for i in favorites_list:  #遍历每一个收藏夹的元数据
        id_ = i['id']
        title = re.sub('([^\u4e00-\u9fa5])', '', i['title']).replace('/','-')
        count = i['media_count']
        f[title] = [id_, count]  #title作为键，id和count作为值
    #     id_list.append(id_)
    #     title_list.append(title)
    #     count_list.append(count)
    # dic = dict(zip(title_list, id_list))
    # print(dic)
    return f


# 获取收藏夹名字
settings = "700 功能性文件/Python脚本设置.md"
setting = str(open(settings, 'r', encoding="utf-8").read()).replace('\n','').replace(' ','')  #读取并替换换行和空格

names = re.findall('##B站同步文件夹(.*?)##', setting)[0].split('-[]')  #正则匹配并列出列表(第一项为空字符串)
names = [i for i in names if i != '']  #去除空项目
f = get_id()
for name in names:  #遍历要同步的b站收藏夹
    # name = 'Obsidian同步收藏夹'
    id_ = f[name][0]
    count = f[name][1]  #收藏夹内视频数量
    num_page = int(count/20)+1  #每20个视频分为一组，求出一共多少组
    for i in range(num_page):
        url = 'https://api.bilibili.com/x/v3/fav/resource/list?media_id={}&pn={}&ps=20&keyword=&order=mtime&type=0&tid=0&platform=web&jsonp=jsonp'.format(id_, i+1)
        path_one = '100 B站视频/{}'.format(name)  #本地收藏夹路径
        ok = bilibili_to_ob(path_one, url)
