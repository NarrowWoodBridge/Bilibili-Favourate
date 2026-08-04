from pathlib import Path
from dataclasses import dataclass, field
from tools_file import readfile

@dataclass
class Config:
    settings: Path = ""  # 配置文件所在的文件夹
    vroot: Path = ""  # 储存所有视频笔记的文件夹
    json_save: Path = field(init=False)  # infoDict.json的路径
    cookie: str = field(init=False)  # B站的cookie
    headers: dict = field(init=False)  # 请求头
    fullEpList: list = field(init=False)  # 全部视频合集的列表
    def __post_init__(self):
        self.json_save = '{}/infoDict.json'.format(self.settings)
        #读取cookies，取得header
        self.cookie = open("{}/cookies.md".format(self.settings), 'r', encoding="utf-8").read()
        self.headers = {
            'referer': 'https://space.bilibili.com',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0',
            'cookie': self.cookie
        }
        #获取全收藏合集的列表、新增全收藏合集的列表
        self.fullEpList = readfile("{}/全收藏合集.md".format(self.settings))
    