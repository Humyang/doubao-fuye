# 夸克网盘 Skill 与 闲鱼 MCP 安装说明

本文说明工作流依赖的两个外部组件怎么装、怎么接到豆包客户端。注意二者**形态不同**：

- **夸克网盘**：豆包官方 Skill + Node.js CLI（不是传统 MCP server），走开放平台 API。
- **闲鱼 MCP（FishClaw）**：标准 MCP server（Python + Playwright），通过 **stdio** 接到豆包自定义连接器。

---

## 一、夸克网盘 Skill（quarkclouddrive）

### 1. 前置条件

- macOS / Linux / Windows
- **Node.js ≥ 16**（`bash scripts/install.sh` 会自动检测，macOS 无 Node 时用 Homebrew 自动装）

### 2. 安装

把 `quarkclouddrive` Skill 目录放到豆包的用户 Skill 目录下（与本工作流 Skill 同级），然后执行：

```bash
cd quarkclouddrive
bash scripts/install.sh
```

`install.sh` 会自动完成：
1. 检测操作系统与 Node.js（缺则自动装）
2. 向夸克开放平台拉取最新 skill zip，解压覆盖 `scripts/`、`references/`、`SKILL.md`
3. 自检 `node scripts/quark-drive.cjs --version`

> **升级**：以后说"更新夸克网盘 skill"也直接跑 `bash scripts/install.sh`（覆盖安装 CLI + 文档），**不要**用 `node scripts/quark-drive.cjs update`（那个只更新 CLI 本体，不更新文档）。

### 3. 授权绑定

首次安装或未绑定时，对豆包说"**授权**绑定夸克网盘"，它会调 `login` 命令拉起授权流程。绑定后：

- 所有 CLI 子命令必须带两个公共参数：
  - `--session-input "用户原始提问逐字复制"`
  - `--session-id "{timestamp}-{random}"`（首次生成后同对话复用，禁止用语义化名字）
- 每次调用 CLI 前先跑一次 `bash scripts/install.sh` 做环境自检。

### 4. 验证

```bash
node scripts/quark-drive.cjs --help
node scripts/quark-drive.cjs search --keyword "测试" --search-type dir \
  --session-input "测试搜索" --session-id "1784000000-a1b2c3"
```

能返回结果即安装成功。

### 5. 卸载（两步，不可逆，需二次确认）

```bash
bash scripts/uninstall.sh     # 撤销授权 + 清 CLI
# 然后手动删除整个 quarkclouddrive 目录
```

---

## 二、闲鱼 MCP（FishClaw）

### 1. 前置条件

- macOS / Linux（Windows 需自行改路径）
- **Python ≥ 3.11**（项目 README 建议 3.12）
- [uv](https://docs.astral.sh/uv/)（推荐，也可 `pip install -e .`）
- 一个**闲鱼账号**（首次需扫码登录）

### 2. 拉代码并装依赖

```bash
git clone <fishclaw-mcp 或 baidu-netdisk-xianyu 仓库>
cd xianyu-mcp
uv sync                                   # 建 .venv 并装依赖
uv run playwright install chromium        # 装浏览器内核
```

依赖清单（见 `pyproject.toml`）：`mcp[cli]`、`playwright`、`playwright-stealth`、`openai`、`python-dotenv`、`requests`。

### 3. 配置环境变量（可选）

```bash
cp .env.example .env
```

| 变量 | 必填 | 说明 |
|------|------|------|
| `AGENT_LLM_API_KEY` | 用 AI 文案/生图时必填 | 阿里云 DashScope Key；手写文案+本地图可不填 |
| `PLAYWRIGHT_HEADLESS` | 建议 `false` | headless 会被风控拦"非法访问" |
| `COOKIES_PATH` | 可选 | 默认 `.cache/cookies/xianyu_cookies.json` |
| `PROXY` | 可选 | 如 `http://127.0.0.1:7890` |

### 4. 接到豆包客户端（自定义连接器 / stdio）

> 关键：传输类型必须选 **STDIO**，不是 HTTP；命令直接指向 venv 里的 python（不要用 `uv run`，GUI 进程里 uv 启动慢会超时）。

1. 打开豆包客户端并登录。
2. 左侧边栏 **「技能·连接器·伙伴」** → 进入「技能·连接器」。
3. 右上角 **「+ 新建」** → **「新建自定义连接器」**，按下表填写：

| 表单字段 | 值 |
|---|---|
| 服务器名称 | `xianyu` |
| 传输类型 | **STDIO** |
| 命令 | `<xianyu-mcp 绝对路径>/.venv/bin/python` |
| 参数（逐个添加） | `server.py` |
| 环境变量 | `PLAYWRIGHT_HEADLESS` = `false` |

示例（把路径换成你本机的）：

```
命令: /Users/you/.../xianyu-mcp/.venv/bin/python
参数: server.py
环境变量: PLAYWRIGHT_HEADLESS=false
```

4. 保存。若提示"连接器运行失败"，到连接器列表点 **「重新启动」**。

### 5. 首次登录

接入后对豆包说"**登录闲鱼**"：
- 会弹出一个 Chromium 窗口，用**闲鱼 App 扫码**登录。
- 登录态自动写到 `.cache/cookies/xianyu_cookies.json`，下次免登。
- 注意：你日常 Chrome 里登录了闲鱼，不代表这个 Playwright 会话已登录。

### 6. 验证

对豆包说：
- "登录闲鱼" → 弹出二维码窗口即连接器 OK。
- 之后可 `search_market`（搜竞品）、`draft_item`（建草稿）、`get_selling_items`（看在售）。

> **本工作流不直接调 MCP 的 `publish_item`**（那个会真点发布、不可撤销），而是用 `scripts/xianyu_draft_simple.py` 建草稿并保持窗口，由你在浏览器里自己核对后点发布。

---

## 三、自动发货平台（xianyu-auto-reply，可选）

只有要"买家拍下后自动收到夸克链接+提取码"时才部署。它是一个独立的 Web 服务，不是 MCP：

- 后端 `backend-web`（FastAPI）监听 `:8089`，**只绑 IPv6**，访问必须用 `http://[::1]:8089`（127.0.0.1 连不上），API 前缀 `/api/v1`。
- 前端 `http://localhost:9000`（admin/admin123）。
- 数据库 MySQL `xianyu_data`（默认 127.0.0.1:3306，root 无密码；可用环境变量 `MYSQL_HOST/PORT/USER/PASSWORD/DB` 覆盖）。
- 后端 venv 在 `<平台根>/backend-web/.venv`。

工作流里本 Skill 通过 `scripts/xianyu_admin_token.py` 直接读数据库 JWT 密钥签发 admin token（跳过有滑动验证的 login 接口），再用 curl 调 `/api/v1/cards` 建卡券。未部署本平台时，工作流只做到"闲鱼草稿 + 人工私聊发货"。

---

## 四、常见问题

| 问题 | 处理 |
|------|------|
| 夸克 CLI 报"未授权/认证/token" | 重新调 `login` 走授权 |
| 闲鱼草稿脚本提示未登录 | 检查 `.cache/cookies/xianyu_cookies.json` 是否存在；对豆包说"登录闲鱼"重新扫码 |
| 豆包连接器"运行失败" | 命令必须用 `.venv/bin/python` 绝对路径，不要用 `uv run`；传输类型切 STDIO |
| headless 访问发布页被拦 | 保持 `PLAYWRIGHT_HEADLESS=false`，有头模式 |
| 描述提交报"不能包含 emoji" | 描述文件必须纯文本、无 emoji |
| 分享链接 7 天后失效 | 重新 share 一次，更新卡券 `text_content` 里的链接+提取码 |
