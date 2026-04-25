#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to Word Document Converter Tool

This module provides a comprehensive tool for converting Markdown files to Word documents.
It supports various Markdown syntax elements including headers, paragraphs, lists, 
code blocks, tables, and more.

Usage Examples:
    # 从文件转换
    converter = MarkdownToWordConverter()
    converter.convert_file('input.md', 'output.docx')
    
    # 直接传入内容转换到文件
    markdown_content = "# Hello\n\nThis is a test."
    converter.convert_content_to_file(markdown_content, 'output.docx')
    
    # 转换为文档对象（不保存文件）
    document = converter.convert_to_document(markdown_content)
    if document:
        document.save('output.docx')
    
    # 命令行使用
    python md2doc.py input.md output.docx
    python md2doc.py --content "# Hello World" output.docx
    python md2doc.py output.docx  # 从标准输入读取

Author: AI Assistant
Date: 2025/10/13
"""

from hashlib import sha256
import os
import re
import logging
import tempfile
import requests
import time
import random
from typing import Optional, Dict, Any, List
from pathlib import Path
from urllib.parse import urlparse
import platform

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.shared import OxmlElement, qn
except ImportError:
    raise ImportError("请安装 python-docx 库: pip install python-docx")
try:
    import markdown
    from markdown.extensions import codehilite, tables, toc
except ImportError:
    raise ImportError("请安装 markdown 库: pip install markdown")
    
try:
    import requests
except ImportError:
    raise ImportError("请安装 requests 库: pip install requests")

try:
    from PIL import Image
except ImportError:
    raise ImportError("请安装 Pillow 库: pip install pillow")


class MarkdownToWordConverter:
    """
    Markdown 转 Word 文档转换器
    
    支持的 Markdown 语法：
    - 标题 (H1-H6)
    - 段落
    - 粗体和斜体
    - 有序和无序列表
    - 代码块和行内代码
    - 表格
    - 链接
    - 图片
    - 引用块
    
    支持的转换方式：
    - convert_file(): 从文件转换到文件
    - convert_text(): 从文本转换到文件
    - convert_to_document(): 从文本转换到文档对象
    - convert_content_to_file(): 直接从内容转换到文件
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, document_title: Optional[str] = None):
        """
        初始化转换器
        
        Args:
            config: 配置字典，包含样式和格式设置
            document_title: 文档标题，将插入到文档最上部分
        """
        self.config = self._get_default_config()
        if config:
            self.config.update(config)
        
        self.document_title = document_title
        self.document = None
        self.logger = self._setup_logger()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'font_name': '宋体',
            'font_size': 12,
            'line_spacing': 1.15,
            'paragraph_spacing_before': 6,
            'paragraph_spacing_after': 6,
            'heading_styles': {
                1: {'size': 18, 'bold': True, 'color': RGBColor(0, 0, 0)},
                2: {'size': 16, 'bold': True, 'color': RGBColor(0, 0, 0)},
                3: {'size': 14, 'bold': True, 'color': RGBColor(0, 0, 0)},
                4: {'size': 13, 'bold': True, 'color': RGBColor(0, 0, 0)},
                5: {'size': 12, 'bold': True, 'color': RGBColor(0, 0, 0)},
                6: {'size': 11, 'bold': True, 'color': RGBColor(0, 0, 0)},
            },
            'code_font': 'Consolas',
            'code_background': RGBColor(245, 245, 245),
            'table_style': 'Table Grid',
            'remove_links': False,  # 是否去除链接
            'remove_images': False,  # 是否去除图片
            'download_delay_min': 1.0,  # 图片下载最小延时（秒）
            'download_delay_max': 3.0,  # 图片下载最大延时（秒）
        }
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def convert_file(self, markdown_file: str, output_file: str, document_title: Optional[str] = None) -> bool:
        """
        转换 Markdown 文件为 Word 文档
        
        Args:
            markdown_file: Markdown 文件路径
            output_file: 输出的 Word 文件路径
            document_title: 文档标题，将插入到文档最上部分
            
        Returns:
            bool: 转换是否成功
        """
        try:
            # 检查输入文件
            markdown_file = os.path.normpath(markdown_file)  # 规范化路径
            if not os.path.exists(markdown_file):
                self.logger.error(f"Markdown 文件不存在: {markdown_file}")
                return False
            
            # 读取 Markdown 内容
            with open(markdown_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            # 设置文档标题（如果提供）
            if document_title:
                self.document_title = document_title
            
            # 转换为 Word 文档
            output_file = os.path.normpath(output_file)  # 规范化路径
            success = self.convert_text(markdown_content, output_file)
            
            if success:
                self.logger.info(f"转换成功: {markdown_file} -> {output_file}")
            else:
                self.logger.error(f"转换失败: {markdown_file}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"转换过程中发生错误: {str(e)}")
            return False
    
    def _convert_markdown_to_document(self, markdown_text: str) -> Optional[Document]:
        """
        核心转换方法：将 Markdown 文本转换为 Word 文档对象
        
        Args:
            markdown_text: Markdown 文本内容
            
        Returns:
            Document: Word 文档对象，转换失败时返回 None
        """
        try:
            # 创建新的 Word 文档
            self.document = Document()
            self._setup_document_styles()
            
            # 添加文档标题（如果提供）
            if self.document_title:
                title_paragraph = self.document.add_paragraph(self.document_title)
                title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                title_paragraph.runs[0].font.size = Pt(24)
                title_paragraph.runs[0].font.bold = True
            
            # 解析 Markdown 内容
            lines = markdown_text.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].rstrip()
                
                # 处理不同类型的内容
                if self._is_heading(line):
                    self._add_heading(line)
                elif self._is_code_block_start(line):
                    i = self._add_code_block(lines, i)
                elif self._is_table_row(line):
                    i = self._add_table(lines, i)
                elif self._is_list_item(line):
                    i = self._add_list(lines, i)
                elif self._is_quote(line):
                    i = self._add_quote(lines, i)
                elif line.strip():  # 非空行作为段落处理
                    # 检查是否是图片（支持有alt文本和无alt文本的格式）
                    img_match = re.search(r'!\[(.*?)\]\((.*?)\)', line.strip())
                    if img_match and not self.config.get('remove_images', False):
                        # 处理图片
                        alt_text, img_url = img_match.groups()
                        self._add_image(img_url, alt_text)
                    elif self.config.get('remove_images', False) and re.search(r'!\[(.*?)\]\((.*?)\)', line.strip()):
                        # 如果配置为去除图片，则跳过包含图片的行
                        pass
                    else:
                        # 检查是否是链接
                        link_match = re.search(r'\[(.*?)\]\((.*?)\)', line.strip())
                        if link_match:
                            if not self.config.get('remove_links', False):
                                # 保留链接文本
                                link_text, link_url = link_match.groups()
                                self._add_paragraph(link_text)
                            # 如果 remove_links 为 True，则完全跳过链接
                        else:
                            # 去除链接标记（如果配置为去除链接）
                            if self.config.get('remove_links', False):
                                line = re.sub(r'\[(.*?)\]\((.*?)\)', '', line)
                            if line.strip():  # 只有非空行才添加
                                self._add_paragraph(line)
                # 空行跳过
                
                i += 1
            
            return self.document
            
        except Exception as e:
            self.logger.error(f"转换 Markdown 为文档对象时发生错误: {str(e)}")
            return None
    
    def convert_text(self, markdown_text: str, output_file: str, document_title: Optional[str] = None) -> bool:
        """
        转换 Markdown 文本为 Word 文档
        
        Args:
            markdown_text: Markdown 文本内容
            output_file: 输出的 Word 文件路径
            document_title: 文档标题，将插入到文档最上部分
            
        Returns:
            bool: 转换是否成功
        """
        try:
            # 设置文档标题（如果提供）
            if document_title:
                self.document_title = document_title
            
            # 使用核心转换方法
            document = self._convert_markdown_to_document(markdown_text)
            if document is None:
                return False
            
            # 保存文档
            document.save(output_file)
            return True
            
        except Exception as e:
            self.logger.error(f"转换文本时发生错误: {str(e)}")
            return False
    
    def convert_to_document(self, markdown_text: str, document_title: Optional[str] = None) -> Optional[Document]:
        """
        转换 Markdown 文本为 Word 文档对象（不保存到文件）
        
        Args:
            markdown_text: Markdown 文本内容
            document_title: 文档标题，将插入到文档最上部分
            
        Returns:
            Document: Word 文档对象，转换失败时返回 None
        """
        # 设置文档标题（如果提供）
        if document_title:
            self.document_title = document_title
        
        # 直接使用核心转换方法
        return self._convert_markdown_to_document(markdown_text)
    
    def convert_content_to_file(self, markdown_content: str, output_file: str, document_title: Optional[str] = None) -> bool:
        """
        直接将 Markdown 内容转换为 Word 文件
        
        Args:
            markdown_content: Markdown 文本内容
            output_file: 输出的 Word 文件路径
            document_title: 文档标题，将插入到文档最上部分
            
        Returns:
            bool: 转换是否成功
        """
        try:
            # 设置文档标题（如果提供）
            if document_title:
                self.document_title = document_title
            
            # 使用核心转换方法
            document = self._convert_markdown_to_document(markdown_content)
            if document:
                document.save(output_file)
                self.logger.info(f"内容转换成功，已保存到: {output_file}")
                return True
            else:
                self.logger.error("内容转换失败")
                return False
                
        except Exception as e:
            self.logger.error(f"保存文档时发生错误: {str(e)}")
            return False
    
    def _setup_document_styles(self):
        """设置文档样式"""
        styles = self.document.styles
        
        # 设置正文样式
        normal_style = styles['Normal']
        normal_font = normal_style.font
        normal_font.name = self.config['font_name']
        normal_font.size = Pt(self.config['font_size'])
        
        # 设置标题样式
        for level, style_config in self.config['heading_styles'].items():
            heading_style_name = f'Heading {level}'
            if heading_style_name in styles:
                heading_style = styles[heading_style_name]
                heading_font = heading_style.font
                heading_font.name = self.config['font_name']
                heading_font.size = Pt(style_config['size'])
                heading_font.bold = style_config['bold']
                heading_font.color.rgb = style_config['color']
    
    def _is_heading(self, line: str) -> bool:
        """判断是否为标题行"""
        return line.strip().startswith('#')
    
    def _add_heading(self, line: str):
        """添加标题"""
        # 计算标题级别
        level = 0
        for char in line:
            if char == '#':
                level += 1
            else:
                break
        
        level = min(level, 6)  # 最多支持 6 级标题
        title_text = line[level:].strip()
        
        # 添加标题
        heading = self.document.add_heading(title_text, level)
        self._format_paragraph(heading, is_heading=True)
    
    def _is_code_block_start(self, line: str) -> bool:
        """判断是否为代码块开始"""
        return line.strip().startswith('```')
    
    def _add_code_block(self, lines: List[str], start_index: int) -> int:
        """添加代码块"""
        i = start_index + 1
        code_lines = []
        
        # 收集代码块内容
        while i < len(lines):
            if lines[i].strip().startswith('```'):
                break
            code_lines.append(lines[i])
            i += 1
        
        # 添加代码块
        code_text = '\n'.join(code_lines)
        code_paragraph = self.document.add_paragraph()
        code_run = code_paragraph.add_run(code_text)
        code_run.font.name = self.config['code_font']
        code_run.font.size = Pt(10)
        
        # 设置代码块背景色（通过样式实现）
        self._set_paragraph_background(code_paragraph)
        
        return i
    
    def _is_table_row(self, line: str) -> bool:
        """判断是否为表格行"""
        return '|' in line.strip()
    
    def _add_table(self, lines: List[str], start_index: int) -> int:
        """添加表格"""
        table_lines = []
        i = start_index
        
        # 收集表格行
        while i < len(lines) and self._is_table_row(lines[i]):
            table_lines.append(lines[i])
            i += 1
        
        if not table_lines:
            return start_index
        
        # 解析表格数据
        table_data = []
        for line in table_lines:
            # 跳过分隔行 (如 |---|---|)
            if re.match(r'^\s*\|[\s\-\|:]+\|\s*$', line):
                continue
            
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            if cells:
                table_data.append(cells)
        
        if not table_data:
            return i - 1
        
        # 创建表格
        rows = len(table_data)
        cols = len(table_data[0])
        table = self.document.add_table(rows=rows, cols=cols)
        table.style = self.config['table_style']
        
        # 填充表格数据
        for row_idx, row_data in enumerate(table_data):
            for col_idx, cell_data in enumerate(row_data):
                if col_idx < cols:
                    table.cell(row_idx, col_idx).text = cell_data
        
        return i - 1
    
    def _is_list_item(self, line: str) -> bool:
        """判断是否为列表项"""
        stripped = line.strip()
        return (stripped.startswith('- ') or 
                stripped.startswith('* ') or 
                stripped.startswith('+ ') or
                re.match(r'^\d+\.\s', stripped))
    
    def _add_list(self, lines: List[str], start_index: int) -> int:
        """添加列表"""
        i = start_index
        list_items = []
        
        # 收集列表项
        while i < len(lines) and self._is_list_item(lines[i]):
            list_items.append(lines[i])
            i += 1
        
        # 添加列表项
        for item in list_items:
            item_text = re.sub(r'^[\s\-\*\+\d\.]+\s*', '', item)
            paragraph = self.document.add_paragraph(item_text, style='List Bullet')
            self._format_paragraph(paragraph)
        
        return i - 1
    
    def _is_quote(self, line: str) -> bool:
        """判断是否为引用"""
        return line.strip().startswith('>')
    
    def _add_quote(self, lines: List[str], start_index: int) -> int:
        """添加引用块"""
        i = start_index
        quote_lines = []
        
        # 收集引用内容
        while i < len(lines) and self._is_quote(lines[i]):
            quote_text = lines[i].strip()[1:].strip()  # 移除 '>' 符号
            quote_lines.append(quote_text)
            i += 1
        
        # 添加引用段落
        quote_text = '\n'.join(quote_lines)
        quote_paragraph = self.document.add_paragraph(quote_text)
        quote_paragraph.style = 'Quote'
        self._format_paragraph(quote_paragraph)
        
        return i - 1
    
    def _add_paragraph(self, line: str):
        """添加普通段落"""
        # 处理行内格式
        formatted_text = self._process_inline_formatting(line)
        paragraph = self.document.add_paragraph()
        
        # 解析并添加格式化文本
        self._add_formatted_text(paragraph, formatted_text)
        self._format_paragraph(paragraph)
    
    def _process_inline_formatting(self, text: str) -> List[Dict[str, Any]]:
        """处理行内格式（粗体、斜体、代码等）"""
        # 这里简化处理，实际可以使用更复杂的解析器
        parts = []
        current_text = text
        
        # 处理粗体 **text**
        bold_pattern = r'\*\*(.*?)\*\*'
        while re.search(bold_pattern, current_text):
            match = re.search(bold_pattern, current_text)
            if match:
                # 添加匹配前的文本
                if match.start() > 0:
                    parts.append({
                        'text': current_text[:match.start()],
                        'bold': False,
                        'italic': False,
                        'code': False
                    })
                
                # 添加粗体文本
                parts.append({
                    'text': match.group(1),
                    'bold': True,
                    'italic': False,
                    'code': False
                })
                
                current_text = current_text[match.end():]
            else:
                break
        
        # 添加剩余文本
        if current_text:
            parts.append({
                'text': current_text,
                'bold': False,
                'italic': False,
                'code': False
            })
        
        return parts if parts else [{'text': text, 'bold': False, 'italic': False, 'code': False}]
    
    def _add_formatted_text(self, paragraph, formatted_parts: List[Dict[str, Any]]):
        """添加格式化文本到段落"""
        for part in formatted_parts:
            run = paragraph.add_run(part['text'])
            if part['bold']:
                run.bold = True
            if part['italic']:
                run.italic = True
            if part['code']:
                run.font.name = self.config['code_font']
                run.font.size = Pt(10)
    
    def _format_paragraph(self, paragraph, is_heading: bool = False):
        """格式化段落"""
        paragraph_format = paragraph.paragraph_format
        paragraph_format.line_spacing = self.config['line_spacing']
        
        if not is_heading:
            paragraph_format.space_before = Pt(self.config['paragraph_spacing_before'])
            paragraph_format.space_after = Pt(self.config['paragraph_spacing_after'])
    
    def _set_paragraph_background(self, paragraph):
        """设置段落背景色（用于代码块）"""
        # 这是一个简化的实现，实际的背景色设置比较复杂
        pass
        
    def _add_image(self, img_url: str, alt_text: str = ""):
        """
        添加图片到文档
        
        Args:
            img_url: 图片URL
            alt_text: 替代文本
        """
        try:
            # 添加随机延时，防止被封IP
            delay_min = self.config.get('download_delay_min',0.1)
            delay_max = self.config.get('download_delay_max', 1)
            delay = random.uniform(delay_min, delay_max)
            # time.sleep(delay)
            # 下载图片
            local_path = self._download_image(img_url)
            if not local_path:
                self.logger.warning(f"无法下载图片: {img_url}")
                return
                
            # 获取图片尺寸并转换格式（如果需要）
            converted_path = self._process_image(local_path)
            if not converted_path:
                self.logger.warning(f"图片处理失败: {local_path}")
                return
                
            try:
                with Image.open(converted_path) as img:
                    width, height = img.size
                    
                # 计算图片的英寸尺寸（假设72 DPI）
                width_inches = width / 72.0
                height_inches = height / 72.0
                
                # 文档可用宽度约为6.5英寸（A4纸宽度减去边距）
                # 文档可用高度约为9英寸（A4纸高度减去边距）
                max_width = 6.5
                max_height = 9.0
                
                # 添加图片到文档
                paragraph = self.document.add_paragraph()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = paragraph.add_run()
                
                # 判断图片是否小于文档大小
                if width_inches <= max_width and height_inches <= max_height:
                    # 图片小于文档大小，使用原尺寸
                    run.add_picture(converted_path, width=Inches(width_inches), height=Inches(height_inches))
                    self.logger.info(f"添加原尺寸图片成功: {img_url} ({width}x{height}px, {width_inches:.2f}x{height_inches:.2f}in)")
                else:
                    # 图片较大，需要缩放
                    is_landscape = width > height
                    
                    if is_landscape:
                        # 横图：固定宽度，高度自动调整
                        run.add_picture(converted_path, width=Inches(6))
                        self.logger.info(f"添加缩放横图成功: {img_url} ({width}x{height}px)")
                    else:
                        # 竖图：固定高度，宽度自动调整
                        run.add_picture(converted_path, height=Inches(6))
                        self.logger.info(f"添加缩放竖图成功: {img_url} ({width}x{height}px)")
                    
            except Exception as img_error:
                self.logger.error(f"处理图片时出错: {str(img_error)}")
                return
            finally:
                # 删除转换后的临时文件（如果与原文件不同）
                if converted_path != local_path:
                    try:
                        os.remove(converted_path)
                    except Exception as e:
                        self.logger.warning(f"删除转换后的临时文件失败: {converted_path}, 错误: {str(e)}")
            
            # 添加图片描述（如果有）
            if alt_text:
                desc_paragraph = self.document.add_paragraph(alt_text)
                desc_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
            # 删除临时文件
            try:
                os.remove(local_path)
            except Exception as e:
                self.logger.warning(f"删除临时图片文件失败: {local_path}, 错误: {str(e)}")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.logger.error(f"添加图片失败: {img_url}")
            self.logger.error(f"错误详情: {str(e)}")
            self.logger.debug(f"完整错误堆栈:\n{error_details}")
    
    def _process_image(self, image_path: str) -> Optional[str]:
        """
        处理图片，确保格式兼容性
        
        Args:
            image_path: 原始图片路径
            
        Returns:
            str: 处理后的图片路径，失败返回None
        """
        try:
            with Image.open(image_path) as img:
                # 检查图片格式
                original_format = img.format
                self.logger.debug(f"原始图片格式: {original_format}")
                
                # 如果是WebP或其他不兼容格式，转换为JPEG
                if original_format in ['WEBP', 'AVIF', 'HEIC', 'HEIF']:
                    # 创建新的临时文件
                    temp_dir = tempfile.gettempdir()
                    base_name = os.path.splitext(os.path.basename(image_path))[0]
                    new_path = os.path.join(temp_dir, f"{base_name}_converted.jpg")
                    
                    # 转换为RGB模式（JPEG不支持透明度）
                    if img.mode in ('RGBA', 'LA', 'P'):
                        # 创建白色背景
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # 保存为JPEG
                    img.save(new_path, 'JPEG', quality=85, optimize=True)
                    self.logger.info(f"图片格式转换成功: {original_format} -> JPEG")
                    return new_path
                else:
                    # 格式兼容，直接返回原路径
                    return image_path
                    
        except Exception as e:
            self.logger.error(f"处理图片失败: {image_path}, 错误: {str(e)}")
            return None
        
    def _download_image(self, url: str) -> Optional[str]:
        """
        下载远程图片到临时文件
        
        Args:
            url: 图片URL
            
        Returns:
            str: 临时文件路径，下载失败返回None
        """
        try:
          
            
            # 验证URL
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                self.logger.warning(f"无效的图片URL: {url}")
                raise ValueError("Invalid URL")
                return None
                
            # 创建临时文件
            temp_dir = tempfile.gettempdir()
            filename = sha256(parsed.path.encode()).hexdigest() +".webp"
            temp_path = os.path.join(temp_dir, filename)
            
            # 设置请求头，模拟浏览器访问
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            # 下载图片
            response = requests.get(url, stream=True, timeout=20, headers=headers)
            response.raise_for_status()
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
                    
            self.logger.debug(f"图片下载成功: {url} -> {temp_path}")
            if not os.path.exists(temp_path):
                raise ValueError(f"图片下载失败: {url} -> {temp_path}")
            return temp_path
            
        except Exception as e:
            self.logger.error(f"下载图片失败: {url}, 错误: {str(e)}")
            raise ValueError(f"下载图片失败: {url}, 错误: {str(e)}")
            return None


def main():
    """主函数 - 命令行工具入口"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='Markdown to Word Converter')
    parser.add_argument('input', nargs='?', help='输入的 Markdown 文件路径（可选，不提供则从标准输入读取）')
    parser.add_argument('output', help='输出的 Word 文件路径')
    parser.add_argument('--config', help='配置文件路径（JSON格式）')
    parser.add_argument('--content', help='直接提供 Markdown 内容（而不是文件路径）')
    parser.add_argument('--title', help='文档标题，将插入到文档最上部分')
    
    args = parser.parse_args()
    
    # 加载配置
    config = None
    if args.config and os.path.exists(args.config):
        import json
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
    
    # 创建转换器
    converter = MarkdownToWordConverter(config)
    
    # 根据输入方式选择转换方法
    success = False
    
    if args.content:
        # 直接使用提供的内容
        success = converter.convert_content_to_file(args.content, args.output, args.title)
        if success:
            print(f"内容转换成功 -> {args.output}")
        else:
            print("内容转换失败")
    elif args.input:
        # 从文件转换
        success = converter.convert_file(args.input, args.output)
        if success:
            print(f"转换成功: {args.input} -> {args.output}")
        else:
            print(f"转换失败: {args.input}")
    else:
        # 从标准输入读取
        try:
            print("请输入 Markdown 内容（按 Ctrl+D 或 Ctrl+Z 结束输入）:")
            markdown_content = sys.stdin.read()
            success = converter.convert_content_to_file(markdown_content, args.output)
            if success:
                print(f"标准输入转换成功 -> {args.output}")
            else:
                print("标准输入转换失败")
        except KeyboardInterrupt:
            print("\n转换被用户中断")
            exit(1)
    
    if not success:
        exit(1)


if __name__ == '__main__':
    main()