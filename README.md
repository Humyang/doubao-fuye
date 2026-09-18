# doubao-fuye：网盘 → 闲鱼 自动发布工作流

把夸克网盘里的虚拟资料，自动走完「查目录 → 创建分享 → 生成封面/描述 → 闲鱼草稿 → 自动发货卡券」整条流水线，并封装成一个豆包 Skill（`netdisk-xianyu-publish`）。

```
夸克网盘(官方 Skill/CLI)  ──┐
                            ├─→ 封面海报 + 商品描述 ─→ 闲鱼草稿(图传满/描述/价格) ─→ 用户点发布
闲鱼 MCP (FishClaw/stdio) ──┘
                                                       ↓
                              自动发货平台(可选) ← 创建卡券(写入分享链接+提取码)
```

## 仓库结构

```
doubao-fuye/
├── README.md                         # 本文件
├── docs/
│   └── MCP_INSTALL.md                # 夸克 + 闲鱼 MCP 详细安装/接入说明
└── skills/
    └── netdisk-xianyu-publish/       # 网盘发布工作流 Skill
        ├── SKILL.md                  # 工作流主文档（四阶段 + 已知坑）
        └── scripts/
            ├── xianyu_draft_simple.py     # 闲鱼草稿：传满图+描述+价格（路径参数化）
            └── xianyu_admin_token.py      # 签发自动发货平台 admin token（路径参数化）
```

## 快速开始（已部署环境）

> 假设夸克网盘 Skill 与闲鱼 MCP 均已安装并授权（见 [docs/MCP_INSTALL.md](docs/MCP_INSTALL.md)）。

1. 把 `skills/netdisk-xianyu-publish/` 整个目录放进豆包的用户 Skill 目录（与 `quarkclouddrive`、`jianying-editor` 等同级）。
2. 重启豆包对话，让它发现新 Skill。
3. 直接对豆包说：
   - "把夸克网盘里「XX合集」的内容生成闲鱼草稿，价格 2.99"
   - 它会自动查目录 → 生成 9 张图 → 写描述 → 跑草稿脚本 → 给你截图确认。
4. 在弹出的浏览器窗口里核对无误后，**你自己点「发布」**（脚本不代点发布、不选分类、不点二维码）。

## 价格与商品默认值

| 项 | 默认值 |
|----|--------|
| 统一售价 | **2.99 元** |
| 可小刀价 | **0.99 元** |
| 商品类型 | 虚拟资料（网盘发货） |
| 折扣 | 后台开启 **20% 折扣** |
| 图片数 | 9 张（1 主图 + 8 细节图，凑满） |
| 描述 | 纯文本、1500 字内、不含 emoji、不含分享链接 |
| 分享有效期 | 7 天（到期需续期/更新卡券） |

## 三个组件速查

| 组件 | 形态 | 安装方式 | 是否必须 |
|------|------|----------|----------|
| 夸克网盘 | 官方 Skill + Node CLI | `bash scripts/install.sh` 后授权 | 必须 |
| 闲鱼 MCP (FishClaw) | Python MCP server (stdio) | `uv sync` + `playwright install chromium` + 豆包自定义连接器 | 必须 |
| 自动发货平台 | FastAPI + MySQL + 前端 | 单独部署 | 可选 |

详细安装步骤见 [docs/MCP_INSTALL.md](docs/MCP_INSTALL.md)。

## 参考项目

本工作流的闲鱼 MCP（FishClaw）与网盘发布流程，参考并基于以下项目整理：

- **[mousepotato/baidu-netdisk-xianyu](https://github.com/mousepotato/baidu-netdisk-xianyu)** — 百度网盘 MCP + 闲鱼 MCP（FishClaw）双 MCP 仓库，含 stdio 接入示例、环境变量模板与免责声明。本仓库的 `xianyu-mcp` 目录结构、Playwright 自动化思路与豆包自定义连接器（STDIO）接法均来源于此。
- **[TnoobT/FishClaw_MCP](https://github.com/TnoobT/FishClaw_MCP)** — 闲鱼 Playwright 自动化 MCP 上游项目（`xianyu-mcp` 的直接参考来源）。
- **夸克网盘 Skill** — 豆包官方 `quarkclouddrive` Skill（Node CLI），通过 `bash scripts/install.sh` 安装与授权。

## 免责声明

本工作流仅供学习交流与个人自用自动化。闲鱼侧通过浏览器自动化（Playwright）操作网页，可能因页面改版、风控、登录态失效而失败；请遵守闲鱼/阿里用户协议与当地法律法规，勿用于批量违规上架。使用后果由使用者自行承担。
