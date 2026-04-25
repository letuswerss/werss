import sys
import os
from colorama import init, Fore, Back, Style
# 确保在Linux下也能正确初始化colorama
if os.name == 'posix':
    os.environ['TERM'] = 'xterm-256color'  # 设置终端类型为支持颜色的终端
init()  # 初始化colorama，确保跨平台支持ANSI颜色
class ColorPrinter:
    """带颜色输出的打印工具类"""
    
    def __init__(self):
        self._fore_color = ''
        self._back_color = ''
        self._style = ''
        self._text = ''
    
    def _reset(self):
        """重置颜色和样式"""
        self._fore_color = ''
        self._back_color = ''
        self._style = ''
        return self
    
    def red(self):
        """设置前景色为红色"""
        self._fore_color = Fore.RED
        return self
    
    def green(self):
        """设置前景色为绿色"""
        self._fore_color = Fore.GREEN
        return self
    
    def yellow(self):
        """设置前景色为黄色"""
        self._fore_color = Fore.YELLOW
        return self
    
    def blue(self):
        """设置前景色为蓝色"""
        self._fore_color = Fore.BLUE
        return self
    
    def magenta(self):
        """设置前景色为洋红色"""
        self._fore_color = Fore.MAGENTA
        return self
    
    def cyan(self):
        """设置前景色为青色"""
        self._fore_color = Fore.CYAN
        return self
    
    def white(self):
        """设置前景色为白色"""
        self._fore_color = Fore.WHITE
        return self
    
    def black(self):
        """设置前景色为黑色"""
        self._fore_color = Fore.BLACK
        return self
    
    def bg_red(self):
        """设置背景色为红色"""
        self._back_color = Back.RED
        return self
    
    def bg_green(self):
        """设置背景色为绿色"""
        self._back_color = Back.GREEN
        return self
    
    def bold(self):
        """设置文本为粗体"""
        self._style = Style.BRIGHT
        return self
    
    def dim(self):
        """设置文本为暗淡"""
        self._style = Style.DIM
        return self
    
    def normal(self):
        """设置文本为普通样式"""
        self._style = Style.NORMAL
        return self
    
    def print(self, text, end='\n', file=sys.stdout):
        """打印带格式的文本"""
        formatted = f"{self._style}{self._back_color}{self._fore_color}{text}{Style.RESET_ALL}"
        print(formatted, end=end, file=file)
        self._reset()
        return self
    
    # 快捷方法
    def print_red(self, text, **kwargs):
        """快捷打印红色文本"""
        self.red().print(text, **kwargs)
    
    def print_green(self, text, **kwargs):
        """快捷打印绿色文本"""
        self.green().print(text, **kwargs)
    
    def print_yellow(self, text, **kwargs):
        """快捷打印黄色文本"""
        self.yellow().print(text, **kwargs)
    
    def print_blue(self, text, **kwargs):
        """快捷打印蓝色文本"""
        self.blue().print(text, **kwargs)
    
    def print_magenta(self, text, **kwargs):
        """快捷打印洋红色文本"""
        self.magenta().print(text, **kwargs)
    
    def print_cyan(self, text, **kwargs):
        """快捷打印青色文本"""
        self.cyan().print(text, **kwargs)

    def print_error(self, text, **kwargs):
        """快捷打印错误信息(红色粗体)"""
        self.red().bold().print(text, **kwargs)
    
    def print_warning(self, text, **kwargs):
        """快捷打印警告信息(黄色粗体)"""
        self.yellow().bold().print(text, **kwargs)
    
    def print_success(self, text, **kwargs):
        """快捷打印成功信息(绿色粗体)"""
        self.green().bold().print(text, **kwargs)
    
    def print_info(self, text, **kwargs):
        """快捷打印信息(蓝色)"""
        self.blue().print(text, **kwargs)

# 创建全局实例方便使用
printer = ColorPrinter()
def print_error(text, **kwargs):
    printer.print_error(text, **kwargs)

def print_info(text, **kwargs):
    printer.print_info(text, **kwargs)
    
def print_warning(text, **kwargs):
    printer.print_warning(text, **kwargs)
def print_success(text, **kwargs):
    printer.print_success(text, **kwargs)