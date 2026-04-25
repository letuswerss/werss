"""
Debug日志工具模块
用于管理调试日志文件的清空和写入
"""
import os
from pathlib import Path

# Debug日志文件路径
DEBUG_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    '.cursor',
    'debug.log'
)

def clear_debug_log():
    """清空debug日志文件"""
    try:
        log_file = Path(DEBUG_LOG_PATH)
        if log_file.exists():
            # 清空文件内容（以写入模式打开并立即关闭）
            log_file.write_text('')
            return True
        else:
            # 如果文件不存在，创建目录（如果不存在）
            log_file.parent.mkdir(parents=True, exist_ok=True)
            return True
    except Exception as e:
        # 如果清空失败，静默处理（不影响主程序运行）
        return False

def write_debug_log(data: dict):
    """写入debug日志（NDJSON格式）"""
    try:
        import json
        log_file = Path(DEBUG_LOG_PATH)
        # 确保目录存在
        log_file.parent.mkdir(parents=True, exist_ok=True)
        # 追加写入
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    except Exception:
        # 如果写入失败，静默处理（不影响主程序运行）
        pass

