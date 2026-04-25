from core.print import print_error,print_info,print_warning
import re
class HtmlTools:
    def remove_html_region(self, html_content: str, patterns: list) -> str:
        """
        使用正则表达式移除HTML中指定的区域内容
        
        Args:
            html_content: 原始HTML内容
            patterns: 正则表达式模式列表，用于匹配需要移除的区域
            
        Returns:
            处理后的HTML内容
        """
        if not html_content or not patterns:
            return html_content
            
        processed_content = html_content
        
        for pattern in patterns:
            try:
                # 使用正则表达式移除匹配的区域
                processed_content = re.sub(pattern, '', processed_content, flags=re.DOTALL | re.IGNORECASE)
            except re.error as e:
                print_error(f"正则表达式错误: {pattern}, 错误信息: {e}")
                continue
            except Exception as e:
                print_error(f"处理HTML区域时发生错误: {e}")
                continue
        
        return processed_content

    def remove_common_html_elements(self, html_content: str) -> str:
        """
        移除常见的HTML元素区域
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            处理后的HTML内容
        """
        if not html_content:
            return html_content
        
        # 常见的需要移除的HTML元素模式
        common_patterns = [
            # 移除script标签及其内容
            r'<script[^>]*>.*?</script>',
            # 移除style标签及其内容
            r'<style[^>]*>.*?</style>',
            # 移除注释
            r'<!--.*?-->',
            # 移除iframe标签
            # r'<iframe[^>]*>.*?</iframe>',
            # 移除noscript标签
            # r'<noscript[^>]*>.*?</noscript>',
            # 移除广告相关的div（包含特定class或id）
            # r'<div[^>]*(?:class|id)=["\'][^"\']*(?:ad|advertisement|banner)[^"\']*["\'][^>]*>.*?</div>',
            # 移除header区域
            # r'<header[^>]*>.*?</header>',
            # 移除footer区域
            # r'<footer[^>]*>.*?</footer>',
            # 移除nav区域
            # r'<nav[^>]*>.*?</nav>',
            # 移除aside区域
            # r'<aside[^>]*>.*?</aside>'
        ]
        return self.remove_html_region(html_content, common_patterns)

    def clean_html(self, html_content: str, 
                             remove_ids: list = [], 
                             remove_classes: list = [],
                             remove_selectors: list = [],
                             remove_xpaths: list = [],
                             remove_attributes: list = [],
                             remove_regx:list=[],
                             remove_normal_tag:bool=False) -> str:
        """清理文章HTML内容，移除不需要的元素
        
        Args:
            html_content: 原始HTML内容
            remove_ids: 要移除的id列表
            remove_classes: 要移除的class列表
            remove_selectors: 要移除的CSS选择器列表
            remove_xpaths: 要移除的XPath列表
            remove_attributes: 要移除的属性列表，格式为 [{'name': 'attr_name', 'value': 'attr_value'}] 或 [{'name': 'attr_name'}]
            remove_regx: 要移除的正则表达式列表
            remove_normal_tag: 是否移除常见的HTML元素
        Returns:
            清理后的HTML内容
        """
        cleaned_content = html_content
        
        # 构建统一的选择器列表
        all_selectors = []
        
        # 添加id选择器
        if remove_ids:
            for selector in remove_ids:
                all_selectors.append({'selector': selector, 'type': 'id'})
        
        # 添加class选择器
        if remove_classes:
            for selector in remove_classes:
                all_selectors.append({'selector': selector, 'type': 'class'})
        
        # 添加CSS选择器
        if remove_selectors:
            for selector in remove_selectors:
                all_selectors.append({'selector': selector, 'type': 'css'})
        
        # 添加XPath选择器
        if remove_xpaths:
            for selector in remove_xpaths:
                all_selectors.append({'selector': selector, 'type': 'xpath'})
        
        # 一次性移除所有元素
        if all_selectors:
            cleaned_content = self.remove_html_elements(cleaned_content, all_selectors)
        
        # 根据属性移除元素
        if remove_attributes:
            cleaned_content = self.remove_elements_by_attributes(cleaned_content, remove_attributes)
        
        # 根据正则表达式移除元素
        if remove_regx:
            cleaned_content=self.remove_html_region(cleaned_content,remove_regx)
        if remove_normal_tag:
            cleaned_content=self.remove_common_html_elements(cleaned_content)
        # 移除空文本元素（排除媒体标签）
        cleaned_content = self.remove_empty_text_elements(cleaned_content)
        

        return cleaned_content

    def remove_elements_by_attributes(self, html_content: str, attributes: list) -> str:
        """根据属性移除HTML元素
        
        Args:
            html_content: 原始HTML内容
            attributes: 属性列表，格式为 [{'name': 'attr_name', 'value': 'attr_value'}] 或 [{'name': 'attr_name'}]
                       如果只提供name，则移除所有包含该属性的元素
                       如果同时提供name和value，则移除属性值匹配的元素
            
        Returns:
            清理后的HTML内容
        """
        try:
            if not html_content or not attributes:
                return html_content
                
            # 导入BeautifulSoup用于HTML解析
            try:
                from bs4 import BeautifulSoup
            except ImportError:
                print_error("BeautifulSoup未安装，无法进行属性过滤")
                return html_content
            
            soup = BeautifulSoup(html_content, 'html.parser')
            removed_count = 0
            
            for attr_config in attributes:
                if not isinstance(attr_config, dict):
                    continue
                    
                attr_name = attr_config.get('name')
                attr_value = attr_config.get('value')
                eq = attr_config.get('eq')
                
                if not attr_name:
                    continue
                
                if attr_value:
                    if eq:
                        # 精确模糊
                        elements = soup.find_all(attrs={attr_name: attr_value})
                    else:
                        # 模糊匹配属性值
                        elements = soup.select(f'[{attr_name}*="{attr_value}"]')
                else:
                    # 只匹配属性名，不关心属性值
                    elements = soup.find_all(attrs={attr_name: True})
                
                # 移除找到的元素
                for element in elements:
                    if element:
                        element.decompose()
                        removed_count += 1
            
            if removed_count > 0:
                print_info(f"根据属性成功移除 {removed_count} 个HTML元素")
            
            return str(soup)
            
        except Exception as e:
            print_error(f"根据属性移除元素失败: {e}")
            return html_content

    def remove_empty_text_elements(self, html_content: str) -> str:
        """移除空文本元素，但排除图片等媒体标签
        
        Args:
            html_content: 原始HTML内容
            
        Returns:
            清理后的HTML内容
        """
        try:
            if not html_content:
                return html_content
                
            # 导入BeautifulSoup用于HTML解析
            try:
                from bs4 import BeautifulSoup
            except ImportError:
                print_error("BeautifulSoup未安装，无法进行空文本过滤")
                return html_content
            
            soup = BeautifulSoup(html_content, 'html.parser')
            removed_count = 0
            
            # 媒体标签列表（这些标签即使没有文本内容也应该保留）
            media_tags = ['img', 'video', 'audio', 'picture', 'source', 'track', 'canvas', 'svg', 'iframe', 'embed', 'object']
            
            # 查找所有可能包含文本的元素
            all_elements = soup.find_all()
            
            for element in all_elements:
                # 跳过媒体标签
                if element.name in media_tags:
                    continue
                
                # 检查元素是否包含媒体标签（图片、视频等），如果包含则保留
                has_media = False
                for media_tag in media_tags:
                    if element.find(media_tag):
                        has_media = True
                        break
                
                # 如果包含媒体标签，保留该元素
                if has_media:
                    continue
                
                # 检查元素是否只包含空白文本或没有文本内容
                if element.string is None:
                    # 检查子元素
                    has_visible_content = False
                    for child in element.descendants:
                        if child.name is None:  # 文本节点
                            text_content = str(child).strip()
                            if text_content:
                                has_visible_content = True
                                break
                        elif child.name not in media_tags:  # 非媒体元素
                            # 检查非媒体元素是否有属性或内容
                            if child.attrs or child.contents:
                                has_visible_content = True
                                break
                    
                    if not has_visible_content:
                        element.decompose()
                        removed_count += 1
                else:
                    # 元素直接包含文本
                    text_content = element.get_text(strip=True)
                    if not text_content:
                        element.decompose()
                        removed_count += 1
            
            if removed_count > 0:
                print_info(f"成功移除 {removed_count} 个空文本元素")
            
            return str(soup)
            
        except Exception as e:
            print_error(f"移除空文本元素失败: {e}")
            return html_content
        

    def _normalize_html(self, html_string: str) -> str:
        """标准化HTML字符串用于比较
        
        Args:
            html_string: 原始HTML字符串
            
        Returns:
            标准化后的HTML字符串
        """
        import re
        # 移除多余的空格和换行符
        normalized = re.sub(r'\s+', ' ', html_string)
        # 移除首尾空格
        normalized = normalized.strip()
        # 标准化属性引号
        normalized = re.sub(r'="([^"]*)"', '="\1"', normalized)
        return normalized

    def remove_html_elements(self, html_content: str, selectors: list) -> str:
        """从HTML代码中移除指定的元素
        
        Args:
            html_content: 原始HTML内容
            selectors: 选择器列表，每个元素可以是：
                      - 字符串：默认使用id选择器
                      - 字典：包含'selector'和'type'键，type支持 "css"、"xpath"、"id"、"class"
                      - 元组：(selector, type)
            
        Returns:
            清理后的HTML内容
        """
        try:
            if not html_content or not selectors:
                return html_content
                
            # 导入BeautifulSoup用于HTML解析
            try:
                from bs4 import BeautifulSoup
            except ImportError:
                print_error("BeautifulSoup未安装，无法进行HTML清理")
                return html_content
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            removed_count = 0
            
            for selector_item in selectors:
                try:
                    # 解析选择器类型
                    if isinstance(selector_item, dict):
                        selector = selector_item.get('selector', '')
                        selector_type = selector_item.get('type', 'id')
                    elif isinstance(selector_item, tuple) and len(selector_item) >= 2:
                        selector = selector_item[0]
                        selector_type = selector_item[1]
                    else:
                        # 默认处理字符串，使用id选择器
                        selector = selector_item
                        selector_type = 'id'
                    
                    if not selector:
                        continue
                        
                    # 根据选择器类型查找元素
                    if selector_type == "css":
                        elements = soup.select(selector)
                    elif selector_type == "xpath":
                        # 注意：BeautifulSoup不支持xpath，需要lxml支持
                        try:
                            from lxml import html
                            # 将BeautifulSoup转换为lxml树
                            lxml_tree = html.fromstring(str(soup))
                            elements = lxml_tree.xpath(selector)
                            
                            # 直接使用lxml移除元素，然后重新构建BeautifulSoup
                            for element in elements:
                                if hasattr(element, 'tag'):
                                    # 直接从lxml树中移除元素
                                    parent = element.getparent()
                                    if parent is not None:
                                        parent.remove(element)
                            
                            # 将修改后的lxml树转换回BeautifulSoup
                            modified_html = html.tostring(lxml_tree, encoding='unicode', pretty_print=False)
                            soup = BeautifulSoup(modified_html, 'html.parser')
                            elements = []  # 元素已在lxml中移除，不需要再处理
                            
                        except ImportError:
                            print_warning("lxml未安装，无法使用xpath选择器")
                            continue
                        except Exception as e:
                            print_error(f"XPath处理失败: {e}")
                            continue
                    elif selector_type == "id":
                        elements = soup.find_all(id=selector)
                    elif selector_type == "class":
                        elements = soup.find_all(class_=selector)
                    else:
                        print_warning(f"不支持的选择器类型: {selector_type}")
                        continue
                    
                    # 移除找到的元素
                    for element in elements:
                        if element:
                            element.decompose()
                            removed_count += 1
                            
                except Exception as e:
                    print_error(f"移除元素失败 (选择器: {selector}, 类型: {selector_type}): {e}")
                    continue
            
            if removed_count > 0:
                print_info(f"成功移除 {removed_count} 个HTML元素")
            
            return str(soup)
            
        except Exception as e:
            print_error(f"HTML清理失败: {e}")
            return html_content
        
htmltools=HtmlTools()