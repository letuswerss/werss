 
from bs4 import BeautifulSoup
import re
from core.log import logger

def format_content(content:str,content_format:str='html'):
    #格式化内容
    # content_format: 'text' or 'markdown' or 'html'
    # content: str
    # return: str
    try:
        if content_format == 'text':
            # 去除HTML标签，保留纯文本
            soup = BeautifulSoup(content, 'html.parser')
            text = soup.get_text().strip()
            content = re.sub(r'\n\s*\n', '\n', text)
        elif content_format == 'markdown':
            # 去除span和font标签，只保留内容
            soup = BeautifulSoup(content, 'html.parser')
            for tag in soup.find_all(['span', 'font','div','strong','b']):
                tag.unwrap()
            for tag in soup.find_all(True):
                if 'style' in tag.attrs:
                  del tag.attrs['style']
                if 'class' in tag.attrs:
                  del tag.attrs['class']
                if 'data-pm-slice' in tag.attrs:
                  del tag.attrs['data-pm-slice']
                if 'data-title' in tag.attrs:
                  # tag.append(tag.attrs['data-title'])
                  del tag.attrs['data-title']
            
                    
            content = str(soup)
            # 替换 p 标签中的换行符为空
            content = re.sub(r'(<p[^>]*>)([\s\S]*?)(<\/p>)', lambda m: m.group(1) + re.sub(r'\n', '', m.group(2)) + m.group(3), content)
            content = re.sub(r'\n\s*\n\s*\n+', '\n', content)
            content = re.sub(r'\*', '', content)
            # print(content)
            from markdownify import markdownify as md
            # 处理图片标签，保留title属性
            soup = BeautifulSoup(content, 'html.parser')
            for img in soup.find_all('img'):
                if 'title' in img.attrs:
                    img['alt'] = img['title']
            content = str(soup)
            # 转换HTML到Markdown
            content = md(content, heading_style="ATX", bullets='-*+', code_language='python')
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
            
    except Exception as e:
        logger.error('format_content error: %s',e)
    return content