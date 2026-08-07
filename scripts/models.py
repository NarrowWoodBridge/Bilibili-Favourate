from pathlib import Path
from dataclasses import dataclass, field
import json, re

from tools_file import readfile

@dataclass
class Config:
    settingsFolder: Path = ""  # 配置文件所在的文件夹
    vroot: Path = ""  # 储存所有视频笔记的文件夹
    json_save: Path = field(init=False)  # infoDict.json的路径
    cookie: str = field(init=False)  # B站的cookie
    headers: dict = field(init=False)  # 请求头
    syncFolders: list = field(default_factory=list)  # 要抓取的收藏夹的名称列表
    fullEpList: list = field(init=False)  # 全部视频合集的列表
    def __post_init__(self):
        self.json_save = '{}/infoDict.json'.format(self.settingsFolder)
        #读取cookies，取得header
        self.cookie = open("{}/cookies.md".format(self.settingsFolder), 'r', encoding="utf-8").read()
        self.headers = {
            'referer': 'https://space.bilibili.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
            'cookie': self.cookie
        }
        #获取要抓取的收藏夹的名称
        script_setting_file = "{}/Python脚本设置.md".format(self.settingsFolder)
        script_setting = str(open(script_setting_file, 'r', encoding="utf-8").read()).replace('\n','').replace(' ','')  #读取并替换换行和空格
        names = re.findall('##B站同步文件夹(.*?)##', script_setting)[0].split('-[]')  #正则匹配并列出列表(第一项为空字符串)
        self.syncFolders = [i for i in names if i != '']  #去除空项目
        #获取全收藏合集的列表、新增全收藏合集的列表
        self.fullEpList = readfile("{}/全收藏合集.md".format(self.settingsFolder))

@dataclass
class User:
    config: Config
    uid: str = "123456"  # 用户id
    name: str = "username"  # 用户名
    infoDict: dict = field(default_factory=dict)  #key为bvid，value为视频信息组成的字典{'title':xx, 'upper':xx......}
    eps: list = field(default_factory=list)  #视频合集最后再一起处理  
    renamed: dict = field(default_factory=dict)  #重命名的文件记录字典，key为原始标题，value为[文件夹路径，修改后的标题]
    #储存当前已抓取的信息字典
    def save_state(self):
        #字典转换
        infoJson = json.dumps(self.infoDict, sort_keys=False, indent=4, separators=(',', ': '))
        #字典储存
        with open(self.config.json_save,"w") as f_save:
            f_save.write(infoJson)

@dataclass
class VideoInfo:
    type: str = ""  #视频类型：单个视频/多page视频/视频合集
    bvid: str = ""
    title: str = ""
    upper: str = ""
    cover: str = ""  #封面
    pages: list = field(default_factory=list)  #多page视频的每一页信息组成的列表
    epData: dict = field(default_factory=dict)  #视频合集的元数据