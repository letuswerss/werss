import uvicorn
from core.config import cfg
from core.print import print_warning, print_info
from core.debug_log import clear_debug_log
import threading
import os

def print_database_source():
    """输出数据库配置来源"""
    # 获取数据库连接字符串（已处理环境变量替换）
    db_config = cfg.get("db") or "sqlite:///data/db.db"
    
    # 检查来源
    db_env = os.getenv("DB")
    db_from_config_raw = cfg.config.get("db") if hasattr(cfg, 'config') and cfg.config else None
    
    # 判断来源优先级：环境变量 > 配置文件 > 默认值
    if db_env:
        # 环境变量存在，检查配置文件是否使用了模板语法
        if db_from_config_raw and db_from_config_raw.startswith("${") and ":-" in db_from_config_raw:
            source = "环境变量 DB（通过配置文件模板）"
        else:
            source = "环境变量 DB"
    elif db_from_config_raw:
        # 检查是否是模板语法
        if db_from_config_raw.startswith("${") and ":-" in db_from_config_raw:
            # 模板语法但环境变量不存在，使用默认值
            source = f"配置文件 {cfg.config_path}（使用默认值）"
        else:
            # 配置文件直接指定
            source = f"配置文件 {cfg.config_path}"
    else:
        source = "默认值"
    
    # 隐藏敏感信息（密码）
    display_value = db_config
    if "@" in display_value:
        # 隐藏密码部分，例如: postgresql://user:password@host/db -> postgresql://user:***@host/db
        parts = display_value.split("@")
        if len(parts) == 2:
            auth_part = parts[0]
            if "://" in auth_part:
                protocol_user = auth_part.split("://")
                if len(protocol_user) == 2:
                    protocol = protocol_user[0] + "://"
                    user_pass = protocol_user[1]
                    if ":" in user_pass:
                        user = user_pass.split(":")[0]
                        display_value = f"{protocol}{user}:***@{parts[1]}"
    
    print_info(f"数据库来源: {source}")
    print_info(f"数据库连接: {display_value}")

if __name__ == '__main__':
    # 清空debug日志文件
    clear_debug_log()
    
    # 确保数据库表存在（无论是否传递 -init 参数）
    from core.db import DB
    try:
        # 确保所有表都存在
        DB.ensure_tables_exist()
    except Exception as e:
        print_warning(f"检查数据库表失败: {e}")
    
    if cfg.args.init=="True":
        import init_sys as init
        init.init()
    
    # 输出数据库来源信息
    print_database_source()
    
    # 检查定时任务配置
    # 注意：如果使用 uvicorn.run("web:app", ...)，定时任务会在 web.py 的 startup 事件中启动
    # 这里只输出配置信息，不启动定时任务，避免重复启动
    job_arg = cfg.args.job == "True"
    enable_job_config = cfg.get("server.enable_job", True)  # 默认启用
    print_info(f"定时任务配置检查: -job参数={job_arg}, server.enable_job={enable_job_config}")
    
    if not job_arg:
        print_warning("未开启定时任务: -job 参数未设置为 True")
    if not enable_job_config:
        print_warning("未开启定时任务: server.enable_job 配置为 False")
    
    # 注意：定时任务将在 web.py 的 startup 事件中启动（如果使用 uvicorn）
    # 这样可以确保每次重新加载时都会重新启动定时任务
    print("启动服务器")
    AutoReload=cfg.get("server.auto_reload",False)
    thread=cfg.get("server.threads",1)
    uvicorn.run("web:app", host="0.0.0.0", port=int(cfg.get("port",8001)),
            reload=AutoReload,
            reload_dirs=['core','web_ui'],
            reload_excludes=['static','web_ui','data'], 
            workers=thread,
            )
    pass