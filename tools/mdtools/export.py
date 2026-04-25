from .md2doc import MarkdownToWordConverter
from core.models import Article
from core.db import DB
from datetime import datetime
from typing import Optional, List
import json
import csv
import zipfile
import os
from core.print import print_success,print_error
from jobs.notice import sys_notice

def process_single_article(art, add_title, remove_images, remove_links, export_md, 
                          export_docx, export_json, export_csv, export_pdf, 
                          docx_path, writer):
    """
    处理单篇文章的导出逻辑
    返回是否成功处理
    """
    from core.content_format import format_content
    from core.common.file_tools import sanitize_filename
    
    # 处理文章内容，如果内容为空则使用空字符串
    content = art.content if art.content else ""
    markdown_content = format_content(content, "markdown") if content else ""
    
    # 转换为文档对象（不保存文件）
    # 只有在需要导出docx时才进行转换
    document = None
    if export_docx or export_pdf:
        if markdown_content:  # 只有当有内容时才转换
            md = MarkdownToWordConverter({
                'remove_links': remove_links,
                'remove_images': remove_images,
                'default_font': 'SimSun'
            })
            if add_title:
                markdown_content = f"# {art.title}\n\n{markdown_content}"
            document = md.convert_to_document(markdown_content, None)
        
    # 检查是否需要导出任何格式的文件
    # 即使没有内容，也可以导出 JSON、CSV 或 MD（空内容）
    if (export_docx and document) or export_md or export_json or export_csv or (export_pdf and document):
        print(art.id, art.title, art.id)
        name = datetime.fromtimestamp(art.publish_time).strftime("%Y%m%d") + "_" + art.title
        filename = sanitize_filename(name) + ".docx"
        json_filename = sanitize_filename(name) + ".json"
        md_filename = sanitize_filename(name) + ".md"
        pdf_filename = sanitize_filename(name) + ".pdf"
        json_content = {
            "id": art.id,
            "url": art.url,
            "title": art.title,
            "pic_url": art.pic_url,
            "description": art.description,
            "status": art.status,
            "publish_time": art.publish_time
        }
        try:
            # 保存json文件（仅在需要时）
            if export_json:
                with open(f"{docx_path}{json_filename}", "w", encoding="utf-8") as f:
                    f.write(json.dumps(json_content))
            
            # 保存md文件（仅在需要时）
            if export_md:
                with open(f"{docx_path}{md_filename}", "w", encoding="utf-8") as f:
                    f.write(markdown_content)

            # 保存为PDF文档（仅在需要时）
            if export_pdf and document:
                # 先保存为临时docx文件，然后转换为PDF
                temp_docx = f'{docx_path}{filename}'
                document.save(temp_docx)
                try:
                    from doc2pdf.dpdf import docx_to_pdf
                    docx_to_pdf(temp_docx, f'{docx_path}{pdf_filename}')
                    # 删除临时docx文件
                    os.remove(temp_docx)
                except Exception as e:
                    print_error(f"PDF转换失败: {e}")
                    # 删除临时文件
                    if os.path.exists(temp_docx):
                        os.remove(temp_docx)
            
            # 保存为Word文档（仅在需要时）
            if export_docx and document:
                document.save(f'{docx_path}{filename}')
                
            # 纪录导出文章列表（仅在需要时）
            if export_csv and writer:
                writer.writerow([art.title, art.url, datetime.fromtimestamp(art.publish_time).strftime("%Y-%m-%d %H:%M:%S")])
            
            exported_files = []
            if export_json: exported_files.append("JSON")
            if export_md: exported_files.append("MD")
            if export_docx and document: exported_files.append("DOCX")
            if export_pdf and document: exported_files.append("PDF")
            if export_csv: exported_files.append("CSV")
            
            print_success(f"文件已保存: {', '.join(exported_files)} - {name}")
            return True
        except Exception as e:
            print_error(f"保存文档失败: {e}")
            return False
    return False

def process_articles(session, mp_id=None,doc_id=None, page_size=10, page_count=1, add_title=True, document_id=None,
                    remove_images=False, remove_links=False, export_md=True, 
                    export_docx=True, export_json=True, export_csv=True, export_pdf=True,
                    docx_path="./data/docs/", writer=None):
    """
    处理文章数据的核心函数
    返回处理的文章数量
    """
    record_count = 0
    i = 0
    is_break=False
    while True:
        if is_break:
            break
        if page_count != 0 and i >= page_count:
            break
            
        # 导入状态常量
        from core.models.base import DATA_STATUS
        
        # 如果指定了 doc_id（导出选中文章），则不要求必须有内容
        # 如果只按 mp_id 查询（导出所有），则要求必须有内容
        # 使用与文章列表相同的过滤条件：status != DELETED（即 status != 1000）
        if doc_id is not None and len(doc_id) > 0:
            # 导出选中文章时，不要求必须有内容，但排除已删除的文章
            query = session.query(Article).where(Article.status != DATA_STATUS.DELETED)
            print(f"导出选中文章模式：不要求有内容，doc_id数量: {len(doc_id)}")
        else:
            # 导出所有文章时，要求必须有内容，并排除已删除的文章
            query = session.query(Article).filter(Article.content != None).where(Article.status != DATA_STATUS.DELETED)
            print(f"导出所有文章模式：要求有内容")
        
        # 如果指定了 doc_id（选中文章导出），则不使用 mp_id 过滤，因为选中的文章可能来自不同公众号
        # 只有在没有 doc_id 的情况下才使用 mp_id 过滤
        if doc_id is None or len(doc_id) == 0:
            # 如果 mp_id 不是 "all"，则按公众号ID过滤
            if mp_id and isinstance(mp_id, str) and mp_id.strip() and mp_id != "all":
                query = query.where(Article.mp_id.in_(mp_id.split(",")))
        
        if doc_id is not None and len(doc_id) > 0:
            # 确保 doc_id 是字符串列表
            doc_id_list = [str(d) for d in doc_id] if doc_id else []
            print(f"导出选中的文章ID（原始）: {doc_id}")
            print(f"导出选中的文章ID（转换后）: {doc_id_list}")
            print(f"doc_id 类型: {type(doc_id)}, doc_id_list 类型: {type(doc_id_list)}")
            query = query.where(Article.id.in_(doc_id_list))
            is_break=True
            # 打印查询的SQL（用于调试）
            print(f"查询条件: status != {DATA_STATUS.DELETED}, id IN {doc_id_list}")   

        query = query.order_by(Article.publish_time.desc(), Article.id.desc())
        if is_break==False:
            query=query.offset(i * page_size).limit(page_size)
        i = i + 1
        arts = query.all()
        
        if doc_id is not None and len(doc_id) > 0:
            print(f"查询到的文章数量: {len(arts) if arts else 0}")
            if arts:
                print(f"查询到的文章ID: {[art.id for art in arts]}")
                print(f"查询到的文章标题: {[art.title for art in arts]}")
            else:
                print(f"警告：没有查询到任何文章！")
                print(f"尝试查询的ID列表: {doc_id_list if 'doc_id_list' in locals() else 'N/A'}")
                # 尝试直接查询一个ID看看是否存在
                if 'doc_id_list' in locals() and doc_id_list and len(doc_id_list) > 0:
                    test_id = doc_id_list[0]
                    test_article = session.query(Article).filter(Article.id == test_id).first()
                    if test_article:
                        print(f"测试：直接查询ID {test_id} 成功")
                        print(f"  文章标题: {test_article.title}")
                        print(f"  文章状态: {test_article.status}")
                        print(f"  文章内容: {'有' if test_article.content else '无'}")
                        print(f"  mp_id: {test_article.mp_id}")
                    else:
                        print(f"测试：直接查询ID {test_id} 失败，该ID不存在")
        
        if arts is None or len(arts) == 0:
            if doc_id is not None and len(doc_id) > 0:
                print(f"错误：导出选中文章时没有查询到任何文章，退出循环")
            break
            
        for art in arts:
            print(f"处理文章: ID={art.id}, 标题={art.title}, 状态={art.status}, 内容={'有' if art.content else '无'}")
            if process_single_article(art, add_title, remove_images, remove_links, 
                                    export_md, export_docx, export_json, export_csv, 
                                    export_pdf, docx_path, writer):
                record_count += 1
                print(f"文章 {art.id} 导出成功，当前计数: {record_count}")
            else:
                print(f"文章 {art.id} 导出失败")
    
    return record_count

def export_md_to_doc(mp_id:Optional[str]=None,doc_id:Optional[List]=None,page_size:int=10,page_count:int=1,add_title=True,remove_images:bool=True,remove_links:bool=False
                     ,export_md:bool=False,export_docx:bool=False,export_json:bool=False,export_csv:bool=False,export_pdf:bool=True,domain="",zip_filename=None,zip_file=True):
    session = None
    csv_file = None
    try:
        session = DB.get_session()
        # 如果 mp_id 是 "all" 或空字符串，使用 "all" 作为目录名
        if mp_id is None:
            raise ValueError("公众号ID不能为空")
        if isinstance(mp_id, str) and not mp_id.strip():
            mp_id = "all"
        # 如果 mp_id 是 "all"，允许导出所有公众号的文章
        docx_path = f"./data/docs/{mp_id}/"
        if not os.path.exists(docx_path):
            os.makedirs(docx_path, exist_ok=True)
        csv_filename = f"{docx_path}articles.csv"
        
        # 初始化CSV文件和writer（仅在需要导出CSV时）
        writer = None
        if export_csv:
            csv_file = open(csv_filename, "w", newline="", encoding="utf-8")
            writer = csv.writer(csv_file)
            writer.writerow(["标题", "链接", "发布时间"])
        
        # 调用独立的文章处理函数
        record_count = process_articles(
            session=session,
            mp_id=mp_id,
            doc_id=doc_id,
            page_size=page_size,
            page_count=page_count,
            add_title=add_title,
            remove_images=remove_images,
            remove_links=remove_links,
            export_md=export_md,
            export_docx=export_docx,
            export_json=export_json,
            export_csv=export_csv,
            export_pdf=export_pdf,
            docx_path=docx_path,
            writer=writer
        )
        
        # 关闭CSV文件（如果打开了）
        if csv_file:
            csv_file.close()
            csv_file = None
            print_success(f"CSV 文件已保存为 {csv_filename}")
        
        # 打包所有导出的文件为zip并删除源文件
        # 即使导出了 0 篇，也创建 zip 文件，这样记录列表里才能看到
        if not zip_filename:
            zip_filename = f"{docx_path}exported_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        else:
            zip_filename = f"{docx_path}{zip_filename}"
            if not zip_filename.endswith('.zip'):
                zip_filename += '.zip'
        if zip_file==False:
            exported_files=[]
            for root, dirs, files in os.walk(docx_path):
                    for file in files:
                        print_success(f"导出文件: {os.path.join(root, file)}")
                        exported_files.append(os.path.join(root, file))
            return exported_files
        try:
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 遍历导出目录中的所有文件
                for root, dirs, files in os.walk(docx_path):
                    for file in files:
                        # 跳过所有zip文件，包括正在创建的zip文件
                        if file.endswith('.zip'):
                            continue
                        file_path = os.path.join(root, file)
                        # 添加文件到zip，使用相对路径
                        arc_name = os.path.relpath(file_path, docx_path)
                        zipf.write(file_path, arc_name)
                        # 删除源文件
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            print_error(f"删除文件失败 {file_path}: {e}")
            
            print_success(f"所有文件已打包为: {zip_filename}")
            print_success(f"源文件已删除")
            
            # 发送系统通知，包含下载链接
            download_link = domain + docx_path + zip_filename.split('/')[-1]
            print_success(f"转换完成{download_link}")
            if record_count > 0:
                sys_notice(f"文章导出完成！共处理 {record_count} 篇文章。下载链接: [点击下载]({download_link})")
            else:
                sys_notice(f"导出完成，但未找到符合条件的文章。下载链接: [点击下载]({download_link})")
        except Exception as e:
            print_error(f"打包文件失败: {e}")
            raise
        
        print_success(f"导出完成，共处理 {record_count} 篇文章")
        return record_count
    except Exception as e:
        print_error(f"导出任务执行失败: {str(e)}")
        import traceback
        print_error(f"错误详情:\n{traceback.format_exc()}")
        raise
    finally:
        # 确保关闭资源
        if csv_file:
            try:
                csv_file.close()
            except Exception:
                pass
        if session:
            try:
                session.close()
            except Exception:
                pass