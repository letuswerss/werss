from sqlalchemy import create_engine, Engine,Text,event,inspect,text
from sqlalchemy.orm import sessionmaker, declarative_base,scoped_session, Session
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Union, Any
from .models import Feed, Article
from .config import cfg
from core.models.base import Base  
from core.print import print_warning,print_info,print_error,print_success
import logging
import os

# SQLAlchemy 日志级别将在 init 方法中根据配置文件的 debug 设置来动态配置

# 声明基类
# Base = declarative_base()

class Db:
    connection_str: Optional[str] = None
    Session: Optional[Any] = None
    engine: Optional[Engine] = None
    session_factory: Optional[Any] = None
    
    def __init__(self,tag:str="默认",User_In_Thread=True):
        self.Session = None
        self.engine = None
        self.User_In_Thread=User_In_Thread
        self.tag=tag
        print_success(f"[{tag}]连接初始化")
        # 优先使用环境变量 DB（CLI/--db-url、Docker 注入），避免无 config.yaml 时误落 sqlite
        db_config = (os.getenv("DB") or "").strip()
        if not db_config:
            db_config = cfg.get("db", default=None, silent=True)
        if not db_config:
            db_config = "sqlite:///data/db.db"
        if isinstance(db_config, str) and db_config.startswith("postgres://"):
            db_config = "postgresql://" + db_config[len("postgres://") :]
        if isinstance(db_config, str):
            self.init(db_config)
        else:
            self.init("sqlite:///data/db.db")
    def get_engine(self) -> Engine:
        """Return the SQLAlchemy engine for this database connection."""
        if self.engine is None:
            raise ValueError("Database connection has not been initialized.")
        return self.engine
    def get_session_factory(self):
        return sessionmaker(bind=self.engine, autoflush=True, expire_on_commit=True, future=True)
    def init(self, con_str: str) -> None:
        """Initialize database connection and create tables"""
        try:
            if con_str is None:
                raise ValueError("Database connection string is None. Please configure 'db' in config.yaml or set DB environment variable.")
            self.connection_str=con_str
            # 检查SQLite数据库文件是否存在
            if con_str.startswith('sqlite:///'):
                db_path = con_str[10:]  # 去掉'sqlite:///'前缀
                if not os.path.exists(db_path):
                    try:
                        os.makedirs(os.path.dirname(db_path), exist_ok=True)
                    except Exception as e:
                        pass
                    open(db_path, 'w').close()
            # 禁用 SQLAlchemy 数据库查询日志（不显示 SQL 语句）
            # 如果需要查看 SQL 日志，可以通过环境变量 DB_ECHO=true 启用
            db_echo_env = os.getenv("DB_ECHO", "").lower() == "true"
            
            # 配置 SQLAlchemy 日志级别
            if db_echo_env:
                # 只有在明确设置 DB_ECHO=true 时才启用 SQL 日志
                logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
                logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
                logging.getLogger('sqlalchemy.dialects').setLevel(logging.INFO)
            else:
                # 默认禁用 SQL 日志（只显示 WARNING 及以上级别）
                logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
                logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
                logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
                # 同时禁用 sqlalchemy.orm 的日志
                logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)
            
            self.engine = create_engine(con_str,
                                     pool_size=5,          # 最小空闲连接数（减少到5）
                                     max_overflow=10,      # 允许的最大溢出连接数（减少到10）
                                     pool_timeout=30,      # 获取连接时的超时时间（秒）
                                     echo=db_echo_env,     # 只有在 DB_ECHO=true 时才启用 SQL 日志
                                     pool_recycle=300,     # 连接池回收时间（秒，增加到5分钟）
                                     pool_pre_ping=True,   # 连接前检查连接是否有效
                                     isolation_level="AUTOCOMMIT",  # 设置隔离级别
                                    #  isolation_level="READ COMMITTED",  # 设置隔离级别
                                    #  query_cache_size=0,
                                     connect_args={"check_same_thread": False} if con_str.startswith('sqlite:///') else {}
                                     )
            self.session_factory=self.get_session_factory()
            
            # 自动执行数据库迁移（检测并创建缺失的表和字段）
            try:
                # 先确保所有表都存在（如果不存在则创建）
                self.ensure_tables_exist()
                # 然后执行迁移（添加缺失的字段）
                self.migrate_tables()
            except Exception as e:
                print_warning(f"自动迁移执行失败（不影响启动）: {e}")
                # 如果迁移失败，尝试直接创建所有表
                try:
                    print_info("尝试直接创建所有表...")
                    self.create_tables()
                except Exception as create_error:
                    print_error(f"创建表也失败: {create_error}")
        except Exception as e:
            print(f"Error creating database connection: {e}")
            raise
    def create_tables(self):
        """Create all tables defined in models"""
        from core.models.base import Base as B # 导入所有模型
        try:
            B.metadata.create_all(self.engine)
            print_success('所有表创建成功！')
        except Exception as e:
            print_error(f"创建表失败: {e}")
            raise
    
    def ensure_tables_exist(self):
        """
        确保所有表都存在，如果不存在则创建
        这个方法会在 migrate_tables 之前调用，确保表结构存在
        适用于 PostgreSQL、MySQL 等数据库
        """
        from core.models.base import Base as B
        from sqlalchemy import inspect as sql_inspect
        
        if self.engine is None:
            raise ValueError("Engine is not initialized")
        
        try:
            # 测试数据库连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            inspector = sql_inspect(self.engine)
            tables_to_create = []
            
            # 检查所有模型表是否存在
            for table_name, table in B.metadata.tables.items():
                try:
                    if not inspector.has_table(table_name):
                        tables_to_create.append((table_name, table))
                except Exception as check_error:
                    # 如果检查失败，假设表不存在，尝试创建
                    print_warning(f"检查表 {table_name} 存在性时出错: {check_error}，将尝试创建")
                    tables_to_create.append((table_name, table))
            
            # 如果有表需要创建，批量创建
            if tables_to_create:
                print_info(f"检测到 {len(tables_to_create)} 个表不存在，开始创建...")
                created_count = 0
                failed_count = 0
                for table_name, table in tables_to_create:
                    try:
                        print_info(f"📦 创建表: {table_name}")
                        table.create(self.engine, checkfirst=True)
                        created_count += 1
                    except Exception as e:
                        print_error(f"创建表 {table_name} 失败: {e}")
                        failed_count += 1
                        # 继续创建其他表，不中断
                
                if created_count > 0:
                    print_success(f"✅ 成功创建 {created_count} 个表")
                if failed_count > 0:
                    print_warning(f"⚠️  {failed_count} 个表创建失败")
            else:
                print_info("✅ 所有表已存在")
        except Exception as e:
            print_error(f"检查表存在性失败: {e}")
            # 如果检查失败，尝试直接创建所有表（使用 create_all，它会自动跳过已存在的表）
            print_info("尝试使用 create_all 创建所有表...")
            try:
                B.metadata.create_all(self.engine, checkfirst=True)
                print_success("✅ 使用 create_all 创建表成功")
            except Exception as create_error:
                print_error(f"create_all 也失败: {create_error}")
                # 不抛出异常，允许应用继续启动（可能表已经存在）
                import traceback
                traceback.print_exc()
    
    def migrate_tables(self):
        """
        自动迁移数据库表结构
        检测模型定义与数据库表结构的差异，自动添加缺失的字段
        """
        from core.models.base import Base as B
        from sqlalchemy import inspect as sql_inspect
        
        if self.engine is None:
            raise ValueError("Engine is not initialized")
        
        try:
            inspector = sql_inspect(self.engine)
            
            # 遍历所有模型
            for table_name, table in B.metadata.tables.items():
                if not inspector.has_table(table_name):
                    # 表不存在，创建表
                    print_info(f"📦 创建新表: {table_name}")
                    table.create(self.engine, checkfirst=True)
                else:
                    # 表存在，检查字段差异
                    existing_columns = {col['name']: col for col in inspector.get_columns(table_name)}
                    model_columns = {col.name: col for col in table.columns}
                    
                    # 检查缺失的字段
                    for col_name, model_col in model_columns.items():
                        if col_name not in existing_columns:
                            # 字段不存在，添加字段
                            self._add_column(table_name, col_name, model_col)
            
            self._upgrade_feeds_mp_cover_to_text(inspector)
            
            print_success('✅ 数据库迁移完成')
        except Exception as e:
            print_error(f"数据库迁移失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_column(self, table_name: str, column_name: str, column: Column):
        """
        添加字段到现有表
        
        Args:
            table_name: 表名
            column_name: 字段名
            column: SQLAlchemy Column 对象
        """
        try:
            # 构建 ALTER TABLE 语句
            if self.connection_str and ('postgresql' in self.connection_str or 'postgres' in self.connection_str):
                # PostgreSQL 语法
                col_type = str(column.type)
                nullable = "NULL" if column.nullable else "NOT NULL"
                default = ""
                
                # 处理默认值
                if column.default is not None:
                    default_val = None
                    try:
                        if hasattr(column.default, 'arg'):
                            default_val = getattr(column.default, 'arg', None)
                        elif hasattr(column.default, 'value'):
                            default_val = getattr(column.default, 'value', None)
                    except (AttributeError, TypeError):
                        pass
                    
                    if default_val is not None:
                        if isinstance(default_val, bool):
                            default = f" DEFAULT {str(default_val).upper()}"
                        elif isinstance(default_val, (int, float)):
                            default = f" DEFAULT {default_val}"
                        else:
                            default = f" DEFAULT '{default_val}'"
                    elif callable(column.default):
                        # 可调用的默认值（如函数）
                        default = ""
                
                alter_sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {col_type} {nullable}{default}'
            else:
                # SQLite/MySQL 语法
                col_type = str(column.type)
                nullable = "" if column.nullable else "NOT NULL"
                default = ""
                
                if column.default is not None:
                    default_val = None
                    try:
                        if hasattr(column.default, 'arg'):
                            default_val = getattr(column.default, 'arg', None)
                        elif hasattr(column.default, 'value'):
                            default_val = getattr(column.default, 'value', None)
                    except (AttributeError, TypeError):
                        pass
                    
                    if default_val is not None:
                        if isinstance(default_val, bool):
                            default = f" DEFAULT {1 if default_val else 0}"
                        elif isinstance(default_val, (int, float)):
                            default = f" DEFAULT {default_val}"
                        else:
                            default = f" DEFAULT '{default_val}'"
                
                alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {col_type} {nullable}{default}"
            
            # 执行 ALTER TABLE
            if self.engine is None:
                raise ValueError("Engine is not initialized")
            
            with self.engine.begin() as conn:
                conn.execute(text(alter_sql))
            
            print_success(f"  ✅ 添加字段: {table_name}.{column_name}")
            
            # 如果是 PostgreSQL，添加注释
            if self.connection_str and ('postgresql' in self.connection_str or 'postgres' in self.connection_str):
                if hasattr(column, 'comment') and column.comment:
                    comment_sql = f"COMMENT ON COLUMN \"{table_name}\".\"{column_name}\" IS '{column.comment}';"
                    try:
                        with self.engine.begin() as conn:
                            conn.execute(text(comment_sql))
                    except:
                        pass  # 注释添加失败不影响主流程
                        
        except SQLAlchemyError as e:
            # 如果字段已存在或其他错误，记录但不中断
            error_msg = str(e)
            if "already exists" in error_msg or "duplicate column" in error_msg.lower():
                print_info(f"  ℹ️  字段已存在: {table_name}.{column_name}")
            else:
                print_warning(f"  ⚠️  添加字段失败 {table_name}.{column_name}: {error_msg}")    
    
    def _upgrade_feeds_mp_cover_to_text(self, inspector) -> None:
        """将 feeds.mp_cover 加宽以容纳 MinIO / 长 URL（模型已为 Text，旧库需 ALTER）。"""
        if self.engine is None or not self.connection_str:
            return
        try:
            if not inspector.has_table("feeds"):
                return
        except Exception:
            return
        cs = self.connection_str.lower()
        try:
            if "postgresql" in cs or "postgres" in cs:
                with self.engine.begin() as conn:
                    conn.execute(text('ALTER TABLE feeds ALTER COLUMN mp_cover TYPE TEXT'))
                print_success("feeds.mp_cover 已升级为 TEXT（PostgreSQL）")
            elif "mysql" in cs or "mariadb" in cs:
                with self.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE feeds MODIFY COLUMN mp_cover MEDIUMTEXT"))
                print_success("feeds.mp_cover 已升级为 MEDIUMTEXT（MySQL）")
        except Exception as e:
            msg = str(e).lower()
            if "already" in msg or "duplicate" in msg or "same" in msg:
                print_info("feeds.mp_cover 列类型升级跳过（可能已是长文本）")
            else:
                print_warning(f"feeds.mp_cover 列类型升级跳过: {e}")
        
    def close(self) -> None:
        """Close the database connection"""
        if self.Session:
            if hasattr(self.Session, 'close'):
                self.Session.close()
            if hasattr(self.Session, 'remove'):
                self.Session.remove()
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    def delete_article(self,article_data:dict)->bool:
        try:
            art = Article(**article_data)
            article_id = getattr(art, 'id', None)
            if article_id:
                article_id = f"{str(getattr(art, 'mp_id', ''))}-{article_id}".replace("MP_WXS_","")
            else:
                return False
            session=DB.get_session()
            article = session.query(Article).filter(Article.id == article_id).first()
            if article is not None:
                session.delete(article)
                session.commit()
                return True
        except Exception as e:
            print_error(f"delete article:{str(e)}")
            pass      
        return False
     
    def add_article(self, article_data: dict,check_exist=False) -> bool:
        try:
            session=self.get_session()
            from datetime import datetime, date
            art = Article(**article_data)
            article_id = getattr(art, 'id', None)
            if article_id:
                article_id = f"{str(getattr(art, 'mp_id', ''))}-{article_id}".replace("MP_WXS_","")
                setattr(art, 'id', article_id)
            
            # 检查文章的发布时间是否早于配置的采集起始时间
            publish_time = getattr(art, 'publish_time', None)
            if publish_time:
                try:
                    # 从配置中获取采集起始时间
                    from core.models.config_management import ConfigManagement
                    config = session.query(ConfigManagement).filter(
                        ConfigManagement.config_key == 'collect_start_date'
                    ).first()
                    
                    if config and config.config_value:
                        try:
                            start_date = datetime.strptime(config.config_value, '%Y-%m-%d').date()
                            # 将 publish_time 转换为日期进行比较
                            if isinstance(publish_time, (int, float)):
                                # 如果是时间戳，转换为日期
                                publish_timestamp = int(publish_time)
                                if publish_timestamp < 10000000000:  # 秒级时间戳
                                    publish_timestamp *= 1000
                                publish_date = datetime.fromtimestamp(publish_timestamp / 1000).date()
                            else:
                                # 如果是 datetime 对象，直接获取日期
                                publish_date = publish_time.date() if hasattr(publish_time, 'date') else publish_time
                            
                            # 如果文章发布时间早于起始时间，跳过保存
                            article_title = getattr(art, 'title', '') or ''
                            if publish_date < start_date:
                                print_info(f"文章发布时间 {publish_date} 早于采集起始时间 {start_date}，跳过保存: {article_title[:50]}")
                                return False
                        except (ValueError, TypeError, AttributeError) as e:
                            # 日期解析失败，记录警告但继续保存
                            print_warning(f"解析采集起始时间或文章发布时间失败: {e}")
                except Exception as e:
                    # 读取配置失败，记录警告但继续保存（使用默认行为）
                    print_warning(f"读取采集起始时间配置失败: {e}")
            
            # 始终检查文章是否已存在（基于ID）
            if not article_id:
                return False
            existing_article = session.query(Article).filter(Article.id == article_id).first()
            if existing_article is not None:
                if check_exist:
                    print_warning(f"Article already exists: {article_id}")
                    return False
                else:
                    # 如果已存在但不要求检查，可以选择更新或跳过
                    # 这里选择跳过，避免重复插入
                    print_info(f"Article already exists, skipping: {article_id}")
                    return False
                
            created_at = getattr(art, 'created_at', None)
            updated_at = getattr(art, 'updated_at', None)
            
            if created_at is None:
                created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if updated_at is None:
                updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if isinstance(created_at, str):
                created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
            if isinstance(updated_at, str):
                updated_at = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
            
            setattr(art, 'created_at', created_at)
            setattr(art, 'updated_at', updated_at)
            
            from core.models.base import DATA_STATUS
            setattr(art, 'status', DATA_STATUS.ACTIVE)
            session.add(art)
            session.flush()  # 先 flush 获取 article.id
            
            # ========== 自动提取标签 ==========
            try:
                # 基于文章内容自动提取标签（会自动创建新标签） 
                auto_extract_enabled = cfg.get("article_tag.auto_extract", True)
                print_info(f"🔍 标签提取配置: auto_extract={auto_extract_enabled}")
                
                if auto_extract_enabled:
                    article_content = getattr(art, 'content', '') or ''
                    content_length = len(article_content)
                    article_title = getattr(art, 'title', '') or ''
                    print_info(f"📝 文章内容长度: {content_length}, 标题: {article_title[:50]}")
                    self._assign_tags_by_extraction(
                        session, 
                        article_id, 
                        article_title, 
                        getattr(art, 'description', '') or '', 
                        article_content
                    )
                else:
                    print_warning("⚠️  标签自动提取已禁用")
            except Exception as tag_error:
                # 标签提取失败不影响文章保存
                print_warning(f"自动提取标签失败: {tag_error}")
                import traceback
                traceback.print_exc()
            # ==========================================
            
            sta=session.commit()
            
        except Exception as e:
            # 处理各种数据库的唯一约束错误
            error_str = str(e)
            article_id_str = article_id if article_id else "unknown"
            if "UNIQUE" in error_str or "Duplicate entry" in error_str or "UniqueViolation" in error_str or "duplicate key" in error_str.lower():
                print_warning(f"Article already exists (duplicate key): {article_id_str}")
                # 尝试回滚，避免事务问题
                try:
                    session.rollback()
                except:
                    pass
                return False
            else:
                print_error(f"Failed to add article: {e}")
                import traceback
                traceback.print_exc()
                try:
                    session.rollback()
                except:
                    pass
                return False
        return True    
        
    def get_articles(self, id:Optional[str]=None, limit:int=30, offset:int=0) -> List[Article]:
        try:
            query = self.get_session().query(Article)
            if id:
                query = query.filter(Article.id == id)
            data = query.limit(limit).offset(offset).all()
            return data
        except Exception as e:
            print(f"Failed to fetch Articles: {e}")
            return []    
             
    def get_all_mps(self) -> List[Feed]:
        """Get all Feed records"""
        try:
            return self.get_session().query(Feed).all()
        except Exception as e:
            print(f"Failed to fetch Feed: {e}")
            return []
            
    def get_mps_list(self, mp_ids:str) -> List[Feed]:
        try:
            ids=mp_ids.split(',')
            data =  self.get_session().query(Feed).filter(Feed.id.in_(ids)).all()
            return data
        except Exception as e:
            print(f"Failed to fetch Feed: {e}")
            return []
    def get_mps(self, mp_id:str) -> Optional[Feed]:
        try:
            data =  self.get_session().query(Feed).filter_by(id= mp_id).first()
            return data
        except Exception as e:
            print(f"Failed to fetch Feed: {e}")
            return None

    def get_faker_id(self, mp_id:str):
        data = self.get_mps(mp_id)
        if data is None:
            return None
        return getattr(data, 'faker_id', None)
    def expire_all(self):
        if self.Session:
            self.Session.expire_all()    
    def bind_event(self,session):
        # Session Events
        @event.listens_for(session, 'before_commit')
        def receive_before_commit(session):
            print("Transaction is about to be committed.")

        @event.listens_for(session, 'after_commit')
        def receive_after_commit(session):
            print("Transaction has been committed.")

        # Connection Events
        @event.listens_for(self.engine, 'connect')
        def connect(dbapi_connection, connection_record):
            print("New database connection established.")

        @event.listens_for(self.engine, 'close')
        def close(dbapi_connection, connection_record):
            print("Database connection closed.")
    def get_session(self):
        """获取新的数据库会话"""
        UseInThread=self.User_In_Thread
        def _session():
            if self.session_factory is None:
                raise ValueError("Session factory is not initialized")
            if UseInThread:
                self.Session=scoped_session(self.session_factory)
                # self.Session=self.session_factory
            else:
                self.Session=self.session_factory
            # self.bind_event(self.Session)
            return self.Session
        
        
        if self.Session is None:
            _session()
        
        if self.Session is None:
            raise ValueError("Session factory is not initialized")
        
        session = self.Session()
        # session.expire_all()
        # session.expire_on_commit = True  # 确保每次提交后对象过期
        # 检查会话是否已经关闭
        if not session.is_active:
            from core.print import print_info
            print_info(f"[{self.tag}] Session is already closed.")
            _session()
            if self.Session is None:
                raise ValueError("Session factory is not initialized")
            return self.Session()
        # 检查数据库连接是否已断开
        try:
            from core.models import User
            # 尝试执行一个简单的查询来检查连接状态
            session.query(User.id).count()
        except Exception as e:
            from core.print import print_warning
            print_warning(f"[{self.tag}] Database connection lost: {e}. Reconnecting...")
            if self.connection_str:
                self.init(self.connection_str)
            _session()
            if self.Session is None:
                raise ValueError("Session factory is not initialized")
            return self.Session()
        return session
    def auto_refresh(self):
        # 定义一个事件监听器，在对象更新后自动刷新
        def receive_after_update(mapper, connection, target):
            print(f"Refreshing object: {target}")
        from core.models import MessageTask,Article
        event.listen(Article,'after_update', receive_after_update)
        event.listen(MessageTask,'after_update',receive_after_update)
        
    def session_dependency(self):
        """FastAPI依赖项，用于请求范围的会话管理"""
        session = self.get_session()
        try:
            yield session
        finally:
            session.remove()
    
    def _assign_tags_by_extraction(self, session, article_id: str, title: str, description: str = "", content: str = ""):
        """使用提取方式自动提取标签并关联（标签存储在 tags 表，通过 article_tags 关联）"""
        try:
            from core.models.tags import Tags
            from core.models.article_tags import ArticleTag
            from core.tag_extractor import TagExtractor
            import uuid
            from datetime import datetime
            
            # 使用全局单例提取器（模型常驻内存）
            from core.tag_extractor import get_tag_extractor
            extractor = get_tag_extractor()

            # 使用 AI 提取标签关键词
            topics = extractor.extract(title, description, content)
            
            if not topics:
                print_warning(f"⚠️  未提取到任何关键词，标题: {title[:50]}")
                return
            
            assigned_count = 0
            auto_create = True  # 始终启用自动创建标签
            
            # 获取文章的发布日期，用于设置标签的创建时间
            article = session.query(Article).filter(Article.id == article_id).first()
            tag_created_at = datetime.now()  # 默认使用当前时间
            if article and article.publish_time:
                try:
                    # 将 publish_time（时间戳）转换为 datetime
                    publish_timestamp = int(article.publish_time)
                    if publish_timestamp < 10000000000:  # 秒级时间戳
                        publish_timestamp *= 1000
                    tag_created_at = datetime.fromtimestamp(publish_timestamp / 1000)
                except Exception as e:
                    print_warning(f"转换文章发布时间失败，使用当前时间: {e}")
                    tag_created_at = datetime.now()
            
            for topic_name in topics:
                # 查找匹配的标签
                tag = session.query(Tags).filter(
                    Tags.name == topic_name,
                    Tags.status == 1
                ).first()
                
                if tag:
                    # 检查是否已存在关联
                    existing = session.query(ArticleTag).filter(
                        ArticleTag.article_id == article_id,
                        ArticleTag.tag_id == tag.id
                    ).first()
                    
                    if not existing:
                        article_tag = ArticleTag(
                            id=str(uuid.uuid4()),
                            article_id=article_id,
                            tag_id=tag.id,
                            created_at=datetime.now(),  # 关联创建时间（当前时间）
                            article_publish_date=tag_created_at  # 文章的发布日期（用于趋势统计）
                        )
                        session.add(article_tag)
                        assigned_count += 1
                elif auto_create:
                    # 自动创建新标签（所有模式都支持）
                    try:
                        import json
                        new_tag = Tags(
                            id=str(uuid.uuid4()),
                            name=topic_name,
                            cover="",
                            intro=f"自动创建的标签：{topic_name}",
                            mps_id="[]",  # 空数组
                            status=1,
                            created_at=tag_created_at,  # 使用文章的发布日期
                            updated_at=tag_created_at   # 使用文章的发布日期
                        )
                        session.add(new_tag)
                        session.flush()  # 获取新标签的 ID
                        
                        article_tag = ArticleTag(
                            id=str(uuid.uuid4()),
                            article_id=article_id,
                            tag_id=new_tag.id,
                            created_at=datetime.now(),  # 关联创建时间（当前时间）
                            article_publish_date=tag_created_at  # 文章的发布日期（用于趋势统计）
                        )
                        session.add(article_tag)
                        assigned_count += 1
                        print_success(f"✅ 自动创建标签: {topic_name}")
                    except Exception as e:
                        print_warning(f"自动创建标签失败: {e}")
            
            if assigned_count > 0:
                print_success(f"✅ 文章 {article_id} 已关联 {assigned_count} 个标签（基于提取）")
            else:
                print_warning(f"⚠️  文章 {article_id} 未关联任何标签")
        except Exception as e:
            print_error(f"提取标签并关联失败: {e}")
            import traceback
            traceback.print_exc()

# 全局数据库实例
DB = Db(User_In_Thread=True)
# 初始化已在 __init__ 中完成，这里不需要再次调用