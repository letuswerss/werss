import re

def sanitize_filename(filename):
    # 定义非法字符的正则表达式模式
    illegal_chars_pattern = r'[\\/*?:"<>|\@|\s]'
    
    # 使用re.sub()函数替换非法字符为空字符串
    sanitized_filename = re.sub(illegal_chars_pattern, '', filename)
    
    return sanitized_filename

def remove_markdown_images(text):
    """
    去除 markdown 文本中的图片标记
    支持两种格式：
    1. ![alt text](image_url)
    2. ![alt text](image_url "title")
    """
    # 匹配 markdown 图片语法的正则表达式
    # ![任意文本](任意链接) 或 ![任意文本](任意链接 "任意标题")
    image_pattern = r'!\[.*?\]\([^)]+\)'
    
    # 使用re.sub()函数移除所有图片标记
    text_without_images = re.sub(image_pattern, '', text)
    
    # 清理可能产生的多余空行
    text_without_images = re.sub(r'\s*', '', text_without_images)
    
    return text_without_images.strip()