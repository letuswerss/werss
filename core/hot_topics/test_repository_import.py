import importlib.util
import sys
import unittest
from pathlib import Path
from types import ModuleType


class TestHotTopicsRepositoryImport(unittest.TestCase):
    def setUp(self):
        self._original_modules = sys.modules.copy()

    def tearDown(self):
        sys.modules.clear()
        sys.modules.update(self._original_modules)

    def test_repository_module_imports_successfully(self):
        core_module = ModuleType("core")
        models_module = ModuleType("core.models")
        sqlalchemy_module = ModuleType("sqlalchemy")
        sqlalchemy_orm_module = ModuleType("sqlalchemy.orm")
        log_module = ModuleType("core.log")
        article_module = ModuleType("core.models.article")
        hot_topics_module = ModuleType("core.models.hot_topics")
        hot_topic_runs_module = ModuleType("core.models.hot_topic_runs")
        hot_topic_articles_module = ModuleType("core.models.hot_topic_articles")

        sqlalchemy_orm_module.Session = object
        article_module.Article = type("Article", (), {})
        hot_topics_module.HotTopic = type("HotTopic", (), {})
        hot_topic_runs_module.HotTopicRun = type("HotTopicRun", (), {})
        hot_topic_articles_module.HotTopicArticle = type("HotTopicArticle", (), {})
        log_module.logger = object()

        sys.modules["core"] = core_module
        sys.modules["core.models"] = models_module
        sys.modules["sqlalchemy"] = sqlalchemy_module
        sys.modules["sqlalchemy.orm"] = sqlalchemy_orm_module
        sys.modules["core.log"] = log_module
        sys.modules["core.models.article"] = article_module
        sys.modules["core.models.hot_topics"] = hot_topics_module
        sys.modules["core.models.hot_topic_runs"] = hot_topic_runs_module
        sys.modules["core.models.hot_topic_articles"] = hot_topic_articles_module

        module_path = Path(__file__).with_name("repository.py")
        spec = importlib.util.spec_from_file_location("test_hot_topics_repository", module_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self.assertTrue(hasattr(module, "create_run"))
        self.assertTrue(hasattr(module, "create_topics"))


if __name__ == "__main__":
    unittest.main()
