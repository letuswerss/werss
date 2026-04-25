#!/usr/bin/env python3
"""
获取 API Token 的简单脚本

使用方法：
    python scripts/get_token.py
    python scripts/get_token.py --username admin --password admin@123
    python scripts/get_token.py --base-url http://localhost:8001
"""
import requests
import argparse
import sys

def get_token(base_url: str, username: str, password: str) -> str:
    """通过登录获取 token"""
    try:
        # 使用表单数据格式（OAuth2PasswordRequestForm）
        login_resp = requests.post(
            f"{base_url}/auth/login",
            data={
                "username": username,
                "password": password
            },
            timeout=10
        )
        
        if login_resp.status_code == 200:
            result = login_resp.json()
            # API 返回格式: {"code": 0, "data": {"access_token": "...", ...}} 或 {"code": 200, ...}
            if result.get('code') == 200 or result.get('code') == 0:
                data = result.get('data', {})
                token = data.get('access_token')
                if token:
                    return token
            # 兼容直接返回 token 的情况
            elif 'access_token' in result:
                return result['access_token']
        
        # 打印错误信息
        print(f"❌ 登录失败: HTTP {login_resp.status_code}")
        try:
            error_info = login_resp.json()
            print(f"   错误信息: {error_info}")
        except:
            print(f"   响应内容: {login_resp.text[:200]}")
        
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ 连接失败: 请确保服务正在运行在 {base_url}")
        return None
    except Exception as e:
        print(f"❌ 异常: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="获取 API Token")
    parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8001/api/v1/wx",
        help="API 基础 URL（默认：http://localhost:8001/api/v1/wx）"
    )
    parser.add_argument(
        "--username",
        type=str,
        default="admin",
        help="登录用户名（默认：admin）"
    )
    parser.add_argument(
        "--password",
        type=str,
        default="admin@123",
        help="登录密码（默认：admin@123）"
    )
    
    args = parser.parse_args()
    
    # 自动补全 API 基础路径
    base_url = args.base_url.rstrip('/')
    if not base_url.endswith('/api/v1/wx'):
        if not base_url.endswith('/api'):
            base_url = f"{base_url}/api/v1/wx"
        elif not base_url.endswith('/api/v1'):
            base_url = f"{base_url}/v1/wx"
        elif not base_url.endswith('/api/v1/wx'):
            base_url = f"{base_url}/wx"
    
    print(f"🔐 正在登录...")
    print(f"   API地址: {base_url}")
    print(f"   用户名: {args.username}")
    
    token = get_token(base_url, args.username, args.password)
    
    if token:
        print(f"\n✅ 登录成功！")
        print(f"\n📋 Token:")
        print(f"{token}")
        print(f"\n💡 使用方法:")
        print(f"   export TOKEN='{token}'")
        print(f"   python scripts/test_keyword_from_db_api.py --token {token}")
        print(f"\n📝 或者在请求头中使用:")
        print(f"   Authorization: Bearer {token}")
        return 0
    else:
        print(f"\n❌ 获取 Token 失败")
        print(f"\n💡 可能的解决方案:")
        print(f"1. 检查服务是否正在运行")
        print(f"   curl {base_url}/auth/login")
        print(f"2. 检查是否已初始化数据库和创建用户")
        print(f"   python main.py -init True")
        print(f"3. 检查用户名和密码是否正确")
        print(f"   当前使用: --username {args.username} --password {args.password}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
