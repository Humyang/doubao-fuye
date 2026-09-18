#!/usr/bin/env python3
"""签发 xianyu-auto-reply 管理平台后端访问 token（admin 账号）。

背景：后端登录接口（/api/v1/auth/login）默认要求滑动验证，不适合脚本直接调用；
本脚本按后端真实校验路径签发 token：
  1. 从 MySQL（xy_system_settings，key=security.jwt_secret_key）读取数据库托管的 JWT 密钥
  2. 写回 backend-web 配置实例（与运行中服务签名密钥一致）
  3. 以 admin（id=1）载荷签发 access token

用法（必须用 backend-web 的 venv 解释器运行）：
  <REPLY_PLATFORM_ROOT>/backend-web/.venv/bin/python xianyu_admin_token.py [有效分钟数，默认120]

路径来源（按优先级）：
  1. 环境变量 REPLY_PLATFORM_ROOT
  2. 命令行第二参数：xianyu_admin_token.py <分钟数> <平台根目录>
  3. 环境变量 MYSQL_HOST / MYSQL_PORT / MYSQL_USER / MYSQL_PASSWORD / MYSQL_DB 覆盖数据库连接

输出：一行 access token，供 `Authorization: Bearer <token>` 使用。
"""
import os
import sys
from datetime import timedelta


def _detect_platform_root(argv) -> str:
    env_root = os.environ.get("REPLY_PLATFORM_ROOT")
    if env_root:
        return env_root
    # 用法: xianyu_admin_token.py [minutes] [platform_root]
    for arg in argv[1:]:
        if "/" in arg:
            return arg
    raise SystemExit(
        "未指定自动发货平台根目录：请设置环境变量 REPLY_PLATFORM_ROOT，"
        "或在命令行末尾传入平台根目录绝对路径。"
    )


ROOT = _detect_platform_root(sys.argv)
sys.path.insert(0, ROOT)
sys.path.insert(0, ROOT + "/backend-web")

import pymysql  # noqa: E402


def load_jwt_secret() -> str:
    conn = pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DB", "xianyu_data"),
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT `value` FROM xy_system_settings WHERE `key`='security.jwt_secret_key'"
    )
    row = cur.fetchone()
    conn.close()
    if not row:
        raise SystemExit("数据库中未找到 security.jwt_secret_key")
    return row[0]


def main() -> int:
    # 分钟数：第一个纯数字参数；平台根目录已在 _detect_platform_root 处理
    minutes = 120
    for arg in sys.argv[1:]:
        if arg.isdigit():
            minutes = int(arg)
            break

    from app.core.config import get_settings  # noqa: E402

    settings = get_settings()
    settings.jwt_secret_key = load_jwt_secret()

    from app.core.security import create_access_token  # noqa: E402

    payload = {"sub": "1", "username": "admin", "role": "ADMIN"}
    print(create_access_token(payload, expires_delta=timedelta(minutes=minutes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
