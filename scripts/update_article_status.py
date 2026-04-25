#!/usr/bin/env python3
"""
更新文章状态脚本
功能：
1. 查看前100篇文章
2. 将所有文章的状态更新为 1
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import DB
from core.models import Article
from core.print import print_info, print_success, print_warning, print_error

def view_articles(limit: int = 100):
    """查看前N篇文章"""
    db = DB()
    session = db.get_session()
    try:
        print_info(f"\n{'='*60}")
        print_info(f"查看前 {limit} 篇文章")
        print_info(f"{'='*60}\n")
        
        articles = session.query(Article).limit(limit).all()
        
        if not articles:
            print_warning("没有找到文章")
            return
        
        print_info(f"找到 {len(articles)} 篇文章：\n")
        print_info(f"{'ID':<30} {'标题':<50} {'状态':<10} {'mp_id':<20}")
        print_info("-" * 110)
        
        for article in articles:
            title = (article.title or '')[:48]
            print_info(f"{article.id:<30} {title:<50} {article.status:<10} {article.mp_id or 'N/A':<20}")
        
        # 统计状态分布
        print_info(f"\n{'='*60}")
        print_info("状态分布统计：")
        print_info(f"{'='*60}\n")
        
        status_count = {}
        for article in articles:
            status = article.status
            status_count[status] = status_count.get(status, 0) + 1
        
        for status, count in sorted(status_count.items()):
            print_info(f"状态 {status}: {count} 篇")
        
    except Exception as e:
        print_error(f"查看文章失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def update_all_article_status(dry_run: bool = False):
    """将所有文章的状态更新为 1"""
    db = DB()
    session = db.get_session()
    try:
        # 先统计当前状态分布
        print_info(f"\n{'='*60}")
        print_info("更新前状态分布：")
        print_info(f"{'='*60}\n")
        
        from sqlalchemy import func
        status_stats = session.query(
            Article.status,
            func.count(Article.id).label('count')
        ).group_by(Article.status).all()
        
        total = 0
        for status, count in status_stats:
            print_info(f"状态 {status}: {count} 篇")
            total += count
        
        print_info(f"\n总计: {total} 篇文章")
        
        if dry_run:
            print_warning("\n[DRY RUN] 模拟模式，不会实际更新数据库")
            print_warning(f"将会更新 {total} 篇文章的状态为 1")
            return
        
        # 执行更新
        print_info(f"\n{'='*60}")
        print_info("开始更新文章状态...")
        print_info(f"{'='*60}\n")
        
        result = session.query(Article).update({Article.status: 1})
        session.commit()
        
        print_success(f"成功更新 {result} 篇文章的状态为 1")
        
        # 验证更新结果
        print_info(f"\n{'='*60}")
        print_info("更新后状态分布：")
        print_info(f"{'='*60}\n")
        
        status_stats_after = session.query(
            Article.status,
            func.count(Article.id).label('count')
        ).group_by(Article.status).all()
        
        for status, count in status_stats_after:
            print_info(f"状态 {status}: {count} 篇")
        
    except Exception as e:
        session.rollback()
        print_error(f"更新文章状态失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='更新文章状态脚本')
    parser.add_argument('--view', type=int, default=100, help='查看前N篇文章（默认100）')
    parser.add_argument('--dry-run', action='store_true', help='模拟模式，不实际更新数据库')
    parser.add_argument('--update', action='store_true', help='执行更新操作')
    
    args = parser.parse_args()
    
    # 查看文章
    if args.view:
        view_articles(args.view)
    
    # 更新状态
    if args.update:
        update_all_article_status(dry_run=args.dry_run)
    elif not args.view:
        # 如果没有指定任何操作，显示帮助
        parser.print_help()

if __name__ == '__main__':
    main()

