# 模块 API

本文记录当前 `scripts/` 中实际使用的接口。项目不是可安装的 Python 包，下面的函数也尚未承诺向后兼容。

## `scripts/models.py`

### `Config(settingsFolder="", vroot="")`

运行配置数据类。初始化时立即读取：

- `<settingsFolder>/cookies.md`
- `<settingsFolder>/Python脚本设置.md`
- `<settingsFolder>/全收藏合集.md`

派生字段：

| 字段 | 类型 | 含义 |
| --- | --- | --- |
| `json_save` | 路径/字符串 | `infoDict.json` 的位置 |
| `cookie` | `str` | Cookie 原文 |
| `headers` | `dict` | Bilibili HTTP 请求头 |
| `syncFolderList` | `list` | 要同步的收藏夹名称 |
| `fullEpList` | `list` | 完整同步的合集名称 |

文件缺失、编码错误或设置区段格式错误会直接抛出异常。

### `User(config)`

保存账号与一轮同步状态的数据类。构造后立即调用 `getFavFolders()`，并为 `config.syncFolderList` 中存在的收藏夹调用 `getFavFolderVideos()`。

主要字段：`infoDict`、`eps`、`renamed`、`syncFolders`。

### `User.save_state() -> None`

将 `infoDict` 格式化为 JSON，并以 UTF-8 覆盖写入 `config.json_save`。中文通过 `ensure_ascii=False` 直接保存，不转换为 `\uXXXX`。

### `VideoInfo`

描述视频元数据的预留数据类，字段包括 `type`、`bvid`、`title`、`upper`、`cover`、`pages`、`epData`。当前主流程仍使用字典，没有创建 `VideoInfo` 实例。

## `scripts/User.py`

### `config` 与 `user`

模块级全局对象：

```python
config = Config(settingsFolder="功能性文件", vroot="B站视频")
user = User(config=config)
```

导入模块会读取配置并触发 `User` 的网络请求。

### `load_state(user) -> None`

若 `infoDict.json` 存在则载入 `user.infoDict`，随后扫描 `config.vroot` 下的 Markdown，通过 YAML `title` 与文件名的差异填充 `user.renamed`。

解析器假设文件包含 `---\n` 分隔的 YAML，并只读取 `类型`、`bvid`、`title`、`upper`、`cover`。格式不符合预期时异常向上传播。

## `scripts/webapi.py`

### `getFavFolders(user) -> dict`

请求 `/x/web-interface/nav` 获取当前账号 `mid`，再请求 `/x/v3/fav/folder/created/list-all` 获取收藏夹。

返回值：

```python
{
    "清洗后的收藏夹名称": {
        "id": 123456,
        "count": 20
    }
}
```

名称通过正则删除基本汉字范围之外的所有字符；清洗后同名的条目会被后出现的条目覆盖。

### `getFavFolderVideos(user, tFavFolder) -> list[dict]`

按每页 20 条请求 `/x/v3/fav/resource/list`，把各页 `medias` 依次追加到列表。`tFavFolder` 必须包含 `id` 和 `count`。

当前页数公式为 `int(count / 20) + 1`，当数量恰好是 20 的倍数时会额外请求一个空页。

### `search(user, bvid, aim, reason="")`

从 `user.infoDict` 查询视频；未命中时请求 `/x/web-interface/view` 并写入缓存。

- `aim == "all"`：返回整条记录。
- 其他 `aim`：返回对应字段，如 `type`、`title`、`upper`、`cover`、`pages` 或 `epData`。
- 响应不含 `data`：打印失败信息并返回 `None`。

视频分为 `single`、`pages`、`ep`。命中缓存时不会校验字段完整性或刷新远端数据；无效 `aim` 会触发 `KeyError`。

## `scripts/main.py`

### `bilibili_to_ob(path_one, item, user) -> None`

处理收藏夹 API 返回的一条 `item`。至少需要 `bvid`、`title`、`upper.name`、`cover`。

- `single`：在收藏夹根目录创建带任务属性的笔记。
- `pages`：建立 `【02.多Page】/<标题>/` 目录笔记和分 P 笔记。
- `ep`：建立 `【01.视频合集】/<合集>/` 目录笔记，把合集汇总到 `user.eps`；完整合集中的既有单视频笔记可能被移动并重写。

函数可能创建目录和文件、移动或删除旧文件，并修改 `user.eps` 与 `user.renamed`。

### `main() -> None`

加载本地状态，遍历 `user.syncFolders`，调用 `bilibili_to_ob()`，统一处理 `user.eps`，最后调用 `user.save_state()`。

模块末尾直接执行 `main()`，没有 `if __name__ == "__main__"` 保护。

## `scripts/mdnote.py`

### `single(user, db, path, checkbox=0, page=0, videoList="", note="", title_file="") -> None`

创建一份 Markdown 笔记。

- `db` 至少需要 `title`、`upper`，可含 `类型`、`bvid`、`cover`。
- `checkbox` 为真时加入任务 YAML，并把自动视频链接写成待办项。
- `page` 非零时给 Bilibili 链接附加 `?p=<page>`。
- `videoList` 非空时原样作为视频区内容。
- `note` 原样写入笔记区。
- `title_file` 可覆盖文件名，但存在性判断仍使用 `db["title"]`。

若 `xexists()` 已找到同原标题笔记，函数直接返回，不更新现有文件。

### `updateList(user, mdfileroute, path_ep, aimlist, opt=0, singlelist=[], title2Dict={}) -> None`

更新合集目录笔记的 `# 视频` 区，并保留标题前内容和 `# 笔记` 区。

- `opt=0`：完整合集，条目使用 Wiki 链接。
- `opt=1`：部分收藏合集；`singlelist` 中的视频使用 Wiki 链接，其余使用网页链接。
- `title2Dict` 必须覆盖 `aimlist` 中每个可用的 `bvid`。

函数可能重命名未被用户手动改名的笔记，并更新 `user.renamed`。它不会删除远端已不存在的旧条目。

### `batchSingleNote(user, alist, path, checkbox=0, title2Dict={}) -> None`

逐个查询 `bvid` 并以 `类型: single-ep` 调用 `single()`。提供 `title2Dict` 时使用合集内标题作为文件名，否则使用视频原标题。

## `scripts/tools_file.py`

### `readfile(file) -> list[str]`

以 UTF-8 按行读取，移除行尾 `\n`，忽略内容恰好为 `"\n"` 的空行。只含空格的行会保留。

### `mkdir(path) -> None`

路径不存在时递归创建目录，已存在时不操作。

### `xexists(user, name, start, aim="none", limit=False, reason="")`

递归搜索 `start` 下的同名笔记或目录，并兼容 `user.renamed` 中的改名记录。

- `aim="file"`：返回 Markdown 路径或 `False`。
- `aim="dir"`：返回目录路径或 `False`。
- 其他值：返回布尔值。
- `limit=True`：只处理 `os.walk()` 的第一层结果。

目录匹配也会检查其内部是否存在同名 Markdown。搜索返回第一个匹配项，标题重复时结果依赖遍历顺序。

## `scripts/tools_str.py`

### `delSuf(self: str, suffix: str) -> str`

当字符串以非空 `suffix` 结尾时移除后缀，否则返回原字符串切片。

### `xreplace(string) -> str`

规范化恰好一对中英文引号，并替换 `/ | : ? < > [ ]`，用于生成文件名。它不是完整的 Windows 文件名清洗器。

### `addStrs(aList, opt=False) -> str`

用换行符连接字符串列表。`opt=False` 删除最后一个换行，`opt=True` 保留。空列表返回空字符串。

### `readmdfile(lines, splitList) -> list[list[str]]`

按顺序用 `splitList` 中的文本切分 Markdown。匹配条件是“分隔文本出现在行内”，命中的分隔行不会进入结果。

函数通过 `pop(0)` 原地修改 `splitList`。调用者通常传入新列表，例如 `['# 视频', '# 笔记']`。
