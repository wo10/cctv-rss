# 央视栏目 RSS（云端版）

用 GitHub Actions 定时调用央视官方接口，生成标准 RSS 并发布到 GitHub Pages。
**完全免费、不占本地电脑、国内可访问。**

## 订阅地址

部署后，你的订阅地址为：

```
https://<你的GitHub用户名>.github.io/<仓库名>/feeds/cjdc.xml
```

索引页（查看所有栏目）：

```
https://<你的GitHub用户名>.github.io/<仓库名>/
```

## 添加新栏目

编辑 `config/columns.json`，加一行：

```json
{
  "id": "栏目拼音缩写",
  "topc": "TOPCxxxxxxxxxxxxxxxx",
  "name": "栏目中文名",
  "url": "栏目主页",
  "desc": "描述"
}
```

其中 `topc`（栏目内部 ID）可从栏目页源码的 `var topicID = 'TOPC...'` 提取。

## 工作原理

1. GitHub Actions 每小时自动运行一次；
2. 运行 `scripts/cctv_rss.py`，读取 `config/columns.json`；
3. 逐个调用央视接口 `api.cntv.cn`，生成 `feeds/<id>.xml`；
4. 推送到 `gh-pages` 分支，由 GitHub Pages 发布。

## 数据来源

央视官方接口：`https://api.cntv.cn/NewVideo/getVideoListByColumn`
