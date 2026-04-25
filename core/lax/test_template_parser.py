import unittest
from template_parser import TemplateParser

class TestTemplateParser(unittest.TestCase):
    """Test cases for TemplateParser class."""

    def test_variable_substitution(self):
        """Test basic variable substitution"""
        template = "Hello, {{name}}!"
        parser = TemplateParser(template)
        context = {"name": "World"}
        result = parser.render(context)
        print(result)
        self.assertEqual(result, "Hello, World!")

    def test_nested_variable_substitution(self):
        """Test nested variable substitution."""
        template = "User: {{user.name}}, Age: {{user.age}}"
        parser = TemplateParser(template)
        context = {"user": {"name": "Alice", "age": 30}}
        result = parser.render(context)
        print(result)
        self.assertEqual(result, "User: Alice, Age: 30")

    def test_if_condition_true(self):
        """Test if condition when true."""
        template = "{% if show %}Visible{% endif %}"
        parser = TemplateParser(template)
        context = {"show": True}
        result = parser.render(context)
        print(result)
        self.assertEqual(result, "Visible")

    def test_if_condition_false(self):
        """Test if condition when false."""
        template = "{% if show %}Visible{% endif %}"
        parser = TemplateParser(template)
        context = {"show": False}
        result = parser.render(context)
        print(result)
        self.assertEqual(result, "")

    def test_if_else_condition(self):
        """Test if-else condition."""
        template = "{% if show %}Visible{% else %}Hidden{% endif %}"
        parser = TemplateParser(template)
        
        # Test when true
        context = {"show": True}
        result = parser.render(context)
        self.assertEqual(result, "Visible")
        
        # Test when false
        context = {"show": False}
        result = parser.render(context)
        print(result)
        self.assertEqual(result, "Hidden")

    def test_for_loop(self):
        """Test for loop."""
        template = "{% for item in items %}{{item}}-{% endfor %}"
        parser = TemplateParser(template)
        context = {"items": [1, 2, 3]}
        result = parser.render(context)
        print(result)
        self.assertEqual(result, "1-\n2-\n3-")

    def test_custom_functions(self):
        """Test custom functions."""
        template = "Result: {{=add(1, 2)}}"
        parser = TemplateParser(template)
        
        def add(a, b):
            return a + b
            
        parser.register_function("add", add)
        result = parser.render({})
        print(result)
        self.assertEqual(result, "Result: 3")

    def test_safe_expression(self):
        """Test safe expression checking."""
        template = "{{=__import__('os').system('ls')}}"
        parser = TemplateParser(template)
        
        result = parser.render({})
        print(result)
        self.assertTrue('[Error:' in result)

    def test_feed_and_articles_template(self):
        """Test feed and articles template."""
        template = """{% if feed is defined %}{
 "feed": "{{ feed.mp_name }}",
 "articles": [
{% for article in articles %}{"title": "{{ article.title }}", "pub_date": "{{ article.publish_time }}"}{% if not loop.last %},{% endif %}
{% endfor %}
 ]
}"""
        parser = TemplateParser(template)
        context = {
            "feed": {"mp_name": "Test Feed"},
            "articles": [
                {"title": "Article 1", "publish_time": "2025-10-24"},
                {"title": "Article 2", "publish_time": "2025-10-25"}
            ]
        }
        result = parser.render(context)
        print(result)
        expected = """{
 "feed": "Test Feed",
 "articles": [
    {"title": "Article 1", "pub_date": "2025-10-24"},
    {"title": "Article 2", "pub_date": "2025-10-25"}
 ]
}"""
        self.assertEqual(result.strip().replace("\n", "").replace(" ", ""), expected.strip().replace("\n", "").replace(" ", ""))

if __name__ == '__main__':
    unittest.main()