"""
模板引擎使用示例

基础用法:
1. 简单变量替换: {{variable}}
2. 条件判断: {% if condition %}...{% endif %}
3. 循环结构: {% for item in items %}...{% endfor %}
"""

from core.lax import TemplateParser


from core.models import Feed, Article
from core.db import DB
def parseTemplate(template:str="", data:dict=None):
    # 示例4: 使用Feed和Article模型数据
    if template == "":
        template = """订阅源信息:
        名称:{{feed.mp_name}}
        描述:{{feed.mp_intro}}
        最新文章:{% if articles %}
        {% for article in articles %}
        - {{ article.title }} ({{ article.pub_date }})
        {% endfor %}
        {% else %}
        暂无文章
        {% endif %}
        """
    parser4 = TemplateParser(template)
    result4 = parser4.render(data)
    return result4
if __name__ == "__main__":
    # 示例4: 使用Feed和Article模型数据
    feed = Feed(mp_name="示例订阅源", mp_intro="这是一个示例订阅源")
    articles = [
        
    ]
    data4 = {"feed": feed, "articles": articles}
    result4 = parseTemplate(template="", data=data4)
    print(result4)