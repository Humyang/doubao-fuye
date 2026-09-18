---
name: netdisk-xianyu-publish
description: 把夸克网盘某个目录/文件的内容一键转成闲鱼可发布商品，并在自动发货管理平台创建自动发货卡券：从夸克网盘查找/列目录、创建夸克分享链接、按内容生成封面海报与商品描述、在闲鱼创建草稿（封面图传满+描述+价格）、创建并绑定自动发货卡券。当用户要求"把网盘 XXX 的内容创建分享/生成封面海报/创建闲鱼草稿/发布到闲鱼""网盘分享到闲鱼卖""自动发布闲鱼商品""创建卡券/自动发货/创建自动发货卡券"等涉及夸克网盘资料转闲鱼商品售卖或自动发货的任务时使用。
---

# 夸克网盘分享 → 封面海报/描述 → 闲鱼草稿 → 自动发货卡券

把用户夸克网盘里某目录的全部内容，走完「查目录 → 列目录 → 创建分享 → 生成封面海报和描述 → 闲鱼草稿（封面图传满+描述+价格）→ 创建自动发货卡券」流程。**不处理商品分类，不点二维码**；发布动作由用户在网页或 App 完成。

## 首次使用前：路径配置（务必先做）

本 skill 把以下本机位置抽成变量，**首次跑通前必须按实际安装位置确认**，并在对话开头用一段"环境事实"固定下来，后续所有命令复用：

| 变量 | 含义 | 如何确定 |
|------|------|----------|
| `$QUARK_SKILL_DIR` | 夸克网盘官方 Skill 根目录（含 `scripts/quark-drive.cjs`） | 见《docs/MCP_INSTALL.md》"夸克网盘 Skill 安装" |
| `$XIANYU_MCP_ROOT` | 闲鱼 MCP（FishClaw）项目根目录（含 `server.py`、`.venv/`） | 见《docs/MCP_INSTALL.md》"闲鱼 MCP 安装" |
| `$WORK_ROOT` | 本 skill 的图片/描述/日志落盘目录（项目工作区） | 用户对话指定的工作目录，如 `~/Doubao/chats/<date>/<chat>/baidu-netdisk-xianyu` |
| `$REPLY_PLATFORM_ROOT` | 自动发货管理平台（xianyu-auto-reply）项目根（含 `backend-web/`） | 仅启用自动发货时需要；见本文阶段四 |
| `$SKILL_DIR` | 本 skill 所在目录（含 `scripts/`） | 即 `skills/netdisk-xianyu-publish/` |

> 脚本会自动从 `$XIANYU_MCP_ROOT/.venv/bin/python` 取解释器；调用草稿脚本时通过 `--project-root` 传入 `$XIANYU_MCP_ROOT`。

**价格默认值（本工作流固定）**：统一售价 **2.99 元**；可小刀价 **0.99 元**；商品类型为**虚拟资料**（网盘发货）；闲鱼后台需开启 **20% 折扣**。用户未指定价格时一律用 2.99。

## 阶段一：夸克网盘查目录 + 创建分享

> 在 `$QUARK_SKILL_DIR` 下执行夸克 CLI。**每次调用 CLI 前先 `bash scripts/install.sh`** 检查环境；所有子命令必须附加 `--session-input "<用户原始提问逐字>"` 与 `--session-id "{timestamp}-{random}"`（session-id 首次生成，同对话复用，禁止语义化命名）。

1. 定位目录：
   - 优先：`node scripts/quark-drive.cjs search --keyword <目录名> --search-type dir --session-input "<原问>" --session-id "<sid>"` 全盘找文件夹，结果取 `fid`
   - 或：`node scripts/quark-drive.cjs browse --parent-fid <父目录FID> --all` 列父目录子项定位
   - **全量结果必须读 CLI 落盘的 artifact jsonl**（stdout 的 result/list 行仅供预览），路径见返回的 `data.file_path`
2. 列目标目录全部条目：`node scripts/quark-drive.cjs browse --parent-fid <目标目录FID> --all`，读 artifact jsonl 拿全量 `filename`/`size`/`fid`——这是后续海报和描述的素材
3. 用户要求"创建分享/分享/发布"时，分享整个目录（用目录 FID）：
   - `node scripts/quark-drive.cjs share <目录FID> --title "<商品名>" --url-type 2 --expired-type 3`
   - `--url-type 2` = 私密链接（提取码由服务端自动生成，以返回 `data.passcode` 为准）；`--expired-type 3` = 7 天有效
   - 用户没要求分享时**不要创建**
4. 分享链接/提取码**只汇报给用户本人**（私下发给买家用），**不写入商品描述**

## 阶段二：生成封面海报 + 商品描述

1. 用 image_gen 生成 **多张** 1:1 商品图（request_list 多个 prompt）：
   - 主图 1 张：必须包含清晰标题（标题文字用中文引号""包裹，文字要素要短，避免生僻长句），风格贴合品类
   - 细节图 6~8 张：以内容实体为主（实物/界面/场景拼贴），可纯视觉不带文字，或带极少量短文字，降低文字渲染出错风险
   - 目标共 **9 张**（闲鱼宝贝图片上限：1 主图 + 8 细节图），凑满即"传满"
2. 用 `curl -sL -o` 把所有图片下载到 **`$WORK_ROOT`**，文件名人工可读，如 `XX合集_封面海报.png`、`XX合集_细节图1.png`、`XX合集_细节图2.png`…
3. 按 browse 内容写描述（1500 字内，**纯文本，禁止 emoji**）：
   - 内容清单（文件名/子目录提炼的关键信息）
   - 如创建了分享：**描述内不写分享链接**，只写"拍下后私聊发链接+提取码"之类的发货说明；链接在交付时单独告知用户
   - 交付/发货说明（虚拟资料，夸克网盘发货，拍下后发链接）
4. 价格：默认 **2.99**（用户未指定时）；可小刀 0.99。交付时告知用户可在 App 修改，并提醒开启 20% 折扣。

## 阶段三：闲鱼草稿（封面图传满 + 描述 + 价格）

1. 把描述写入 UTF-8 文本文件（多行描述用文件传参最稳），落到 `$WORK_ROOT`
2. 后台运行草稿脚本（**run_in_background=true**；脚本会自动切换 venv 解释器）：
   ```bash
   "$XIANYU_MCP_ROOT/.venv/bin/python" "$SKILL_DIR/scripts/xianyu_draft_simple.py" \
     --project-root "$XIANYU_MCP_ROOT" \
     --poster "$WORK_ROOT/主图.png,$WORK_ROOT/细节图1.png,$WORK_ROOT/细节图2.png,..." \
     --description-file "$WORK_ROOT/<商品名>_商品描述.txt" \
     --price 2.99
   ```
   脚本内部自动：加载 Cookie → 登录检查 → 进发布页 → 上传全部封面图（尽量传满 9 张）→ 填描述 → 填价格 → 截图 → 保持窗口存活。**不做分类选择、不点二维码**。
3. 轮询后台任务 stdout，直到出现 `截图: <path>`
4. 验证（交付前必须做）：
   - 日志 `$XIANYU_MCP_ROOT/logs/xianyu_tools_YYYYMMDD.log` 应含 `已从 .../xianyu_cookies.json 加载 Cookies` 与 `登录状态有效`；若缺 Cookie 加载行说明登录态未带入，检查 Cookie 路径
   - Read 截图确认：封面图已全部上传（主图+细节图）、描述已填（无分享链接、无 emoji）、价格正确
5. 交付：present_files 依次交付 ① 主图海报 ② 细节图们 ③ 草稿实况截图；告知用户"窗口保持打开，可在页面点发布（或按需用闲鱼 App 发布）"。**不要**停掉后台任务（停掉会关浏览器窗口）。

## 阶段四：创建自动发货卡券（xianyu-auto-reply 平台，可选）

> 仅当用户部署了自动发货管理平台时执行；未部署则跳过本阶段，发货由人工私聊完成。平台要求见《docs/MCP_INSTALL.md》"自动发货平台（可选）"。

1. 签发 admin 访问 token（**登录接口有滑动验证，不要走 login API**）：
   ```bash
   "$REPLY_PLATFORM_ROOT/backend-web/.venv/bin/python" \
     "$SKILL_DIR/scripts/xianyu_admin_token.py" 120
   ```
   脚本自动读数据库托管 JWT 密钥并用 admin（id=1）载荷签发，输出一行 token。所有 API 请求带 `Authorization: Bearer <token>`。
2. 创建卡券（text 类型，卡券名沿用「<商品名>-发货」格式）：
   ```bash
   curl -s -X POST "http://[::1]:8089/api/v1/cards" \
     -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
     -d '{"name":"<商品名>-发货","type":"text","description":"<商品名>自动发货","enabled":true,"delay_seconds":0,"use_no_logistics_form":false,
          "text_content":"亲，感谢购买！<商品名>资源已备好：\n下载方式：请先在应用商店搜索下载「夸克」APP（电脑端可访问 https://pan.quark.cn 网页版），收到链接后用提取码打开并转存到自己网盘，再下载安装。\n链接：<夸克分享链接>\n提取码：<提取码>\n分享链接7天有效，请尽快转存。如有安装问题或打不开，随时联系客服~"}'
   ```
   成功返回 `{"id": N, "message": "卡券创建成功"}`。**分享链接+提取码必须写入卡券内容**（买家自动收到）；这与商品描述相反（描述不写链接）。
3. 绑定商品：商品**发布并同步进平台**（`xy_catalog_items` 有对应 item_id）后才绑定；未发布时 item_id 留空，发布后补绑：
   ```bash
   curl -s -X PUT "http://[::1]:8089/api/v1/cards/{card_id}/items" \
     -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
     -d '{"item_ids":["<商品item_id>"]}'
   ```
4. 验证：`GET /api/v1/cards/{card_id}` 确认 name/type/enabled/text_content 正确；或查库 `SELECT id,name,item_id,text_content FROM xy_cards WHERE id=N`

## 已知坑（必读）

- **夸克 CLI 前置**：每次调用前先 `bash scripts/install.sh`；命令必须带 `--session-input`（用户原始提问逐字复制）与 `--session-id`（`{timestamp}-{random}`，同对话复用）
- **夸克结果消费**：搜索/浏览的 stdout 仅预览，后续操作必须读返回 `data.file_path` 的 artifact jsonl 全量数据
- **夸克分享**：私密链接（`--url-type 2`）的提取码由服务端自动生成，不可自定，以返回 `data.passcode` 为准；分享地址需以可点击 Markdown 链接展示，禁止代码块包裹；**默认 7 天有效，到期需更新卡券内容或续期分享**
- **平台后端只绑 IPv6**：API 一律 `http://[::1]:8089`，用 127.0.0.1 会 HTTP 000 连不上
- **登录有滑动验证**：不要走 `/api/v1/auth/login`，用 `xianyu_admin_token.py` 签发 token；token 默认 120 分钟有效，过期重新签发
- **卡券与描述相反**：商品描述**不写**分享链接（拍下后私聊），卡券内容**必须写**分享链接+提取码（买家自动收到）
- **发货引导话术**：统一引导「下载夸克APP」——官方 App 名称就是「夸克」（内含网盘），卡券/描述/海报文案一律写「搜索下载夸克APP」，**禁止写「夸克网盘APP」**；电脑端网页版可访问 https://pan.quark.cn
- **Cookie 路径**：闲鱼 cookie 由 `--project-root` 推导为 `<XIANYU_MCP_ROOT>/.cache/cookies/xianyu_cookies.json`；首次需在豆包连接器里让闲鱼 MCP `login` 扫码生成
- **描述不含 emoji**：闲鱼网页版禁止描述含 emoji（页面红字提示"商品描述不能包含emoji"），描述文件必须纯文本
- **分类与二维码不再处理**：网页版分类字段可能被页面自动推荐（如"游戏机"），脚本不去改分类、不点「扫码去APP发布」；用户自行决定分类并在页面发布
- **图片传满**：闲鱼宝贝图片上限 9 张（1 主图 + 8 细节图）。`_upload_image` 支持多张（逗号/换行分隔），每张上传后等待数秒，逐张确认成功
- **有头模式 + Windows UA**：工具已内置；headless 访问发布页会被风控拦截（"非法访问"）
- **窗口存活**：草稿脚本自带 keep-alive，用 run_in_background 启动后不要等待结束
