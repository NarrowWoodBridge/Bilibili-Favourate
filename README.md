# Bilibili 收藏夹同步到 Obsidian

把当前 Bilibili 账号中选定的收藏夹同步为本地 Markdown 笔记，供 Obsidian 浏览、勾选和继续记录学习内容。

项目基于 [nimamxd25/Obsidian-PythonScript](https://github.com/nimamxd25/Obsidian-PythonScript) 继续维护。

## 功能

- 同步普通视频、多 P 视频和视频合集。
- 为视频生成带 YAML 属性、封面和 Bilibili 链接的 Markdown 笔记。
- 区分“全部收藏”和“部分收藏”的视频合集。
- 尽量识别用户手动改名的旧笔记，并在刷新合集目录时保留链接。
- 使用 `infoDict.json` 缓存已经查询过的视频元数据。

## 快速开始

项目目前是直接运行的 Python 脚本。请在仓库根目录执行：

```powershell
python -m pip install requests
Copy-Item "功能性文件/cookies.example.md" "功能性文件/cookies.md"
python scripts/main.py
```

运行前还需要：

1. 将自己的 Bilibili Cookie 写入 `功能性文件/cookies.md`。
2. 在 `功能性文件/Python脚本设置.md` 中填写要同步的收藏夹。
3. 按需在 `功能性文件/全收藏合集.md` 中逐行填写需要完整同步的合集名称。

路径均按当前工作目录解析，因此必须从仓库根目录启动。若启动失败或同步结果异常，请先阅读[已知问题](docs/known-issues.md)。

## 文档

- [文档导航](docs/README.md)
- [快速开始与配置](docs/getting-started.md)
- [数据与输出格式](docs/data-and-output.md)
- [架构与同步流程](docs/architecture.md)
- [模块 API](docs/api.md)
- [已知问题与安全提示](docs/known-issues.md)

## 相关演示

- [同步 B 站视频收藏夹到 Obsidian](https://www.bilibili.com/video/BV1C34y177We)
- [同步 B 站视频笔记到 Obsidian](https://www.bilibili.com/video/BV1z541197jf)
- [使用 Obsidian 追更 B 站 UP](https://www.bilibili.com/video/BV1Mr4y147HN)
