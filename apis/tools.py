from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask
from pydantic import BaseModel, Field
from core.auth import get_current_user
from core.db import DB
from .base import success_response, error_response,BaseResponse
from datetime import datetime
from typing import Optional, List, Dict, Any
import os
import threading
import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

# 导入导出工具
from tools.mdtools.export import export_md_to_doc, process_articles

router = APIRouter(prefix="/tools", tags=["工具"])

# 补充缺失标签：后台任务进度（单进程内存；多 worker 需改为 Redis 等）
_MISSING_TAG_JOBS_LOCK = threading.Lock()
_MISSING_TAG_JOBS: Dict[str, Dict[str, Any]] = {}


def _query_missing_tag_article_ids() -> List[str]:
    from sqlalchemy import exists, or_
    from core.models.article import Article
    from core.models.article_tags import ArticleTag
    from core.models.base import DATA_STATUS

    session = DB.get_session()
    try:
        no_tag_row = ~exists().where(ArticleTag.article_id == Article.id)
        rows = (
            session.query(Article.id)
            .filter(no_tag_row)
            .filter(
                or_(
                    Article.status != DATA_STATUS.DELETED,
                    Article.status.is_(None),
                    Article.status == 0,
                ),
                Article.title.isnot(None),
                Article.title != "",
            )
            .all()
        )
        return [str(row.id) for row in rows]
    finally:
        session.close()


def _missing_tags_worker(job_id: str, article_ids: List[str]) -> None:
    from core.models.article import Article
    from core.models.article_tags import ArticleTag
    from core.models.tags import Tags
    from core.print import print_error

    success_count = 0
    error_count = 0
    total = len(article_ids)

    try:
        for idx, article_id in enumerate(article_ids, start=1):
            session = DB.get_session()
            try:
                try:
                    article = session.query(Article).filter(Article.id == article_id).first()
                    if not article:
                        error_count += 1
                    elif not article.title:
                        error_count += 1
                    else:
                        old_tags = session.query(ArticleTag).filter(
                            ArticleTag.article_id == article_id
                        ).all()
                        for old_tag in old_tags:
                            session.delete(old_tag)
                        session.flush()

                        content = article.content if hasattr(article, "content") and article.content else ""
                        description = article.description if article.description else ""

                        try:
                            DB._assign_tags_by_extraction(
                                session=session,
                                article_id=article_id,
                                title=article.title,
                                description=description,
                                content=content,
                            )
                            session.commit()
                        except Exception as ext_e:
                            session.rollback()
                            print_error(f"提取过程报错: {ext_e}")

                        success_count += 1
                except Exception as e:
                    session.rollback()
                    error_count += 1
                    print_error(f"重新提取标签失败 [文章ID: {article_id}]: {e}")
            finally:
                session.close()

            with _MISSING_TAG_JOBS_LOCK:
                j = _MISSING_TAG_JOBS.get(job_id)
                if j:
                    j["processed"] = idx
                    j["success_count"] = success_count
                    j["error_count"] = error_count

        with _MISSING_TAG_JOBS_LOCK:
            j = _MISSING_TAG_JOBS.get(job_id)
            if j:
                j["status"] = "done"
                j["processed"] = total
                j["finished_at"] = time.time()
                j["message"] = f"成功处理 {success_count} 篇文章，失败 {error_count} 篇"
    except Exception as e:
        from core.print import print_error as _pe
        _pe(f"补充缺失标签任务异常 [job={job_id}]: {e}")
        with _MISSING_TAG_JOBS_LOCK:
            j = _MISSING_TAG_JOBS.get(job_id)
            if j:
                j["status"] = "error"
                j["finished_at"] = time.time()
                j["message"] = str(e)


# Schema 模型定义
class ReExtractTagsRequest(BaseModel):
    """批量重新提取标签请求模型"""
    article_ids: List[str] = Field(..., description="要重新提取标签的文章ID列表")

    class Config:
        json_schema_extra = {
            "example": {
                "article_ids": ["1", "2", "3"]
            }
        }


@router.post("/extract_tags", summary="批量重新提取标签")
async def re_extract_tags(
    request: ReExtractTagsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    批量重新提取标签。

    - 传入具体文章 ID：先删旧标签关联再重新提取。
    - `["__all__"]`：对库内未删除文章全量重提（删旧再提）。
    - `["__missing__"]`：仅对「尚无任何标签关联」的文章补充提取（不删已有标签，无标签时等价于直接提）。
    """
    try:
        if not request.article_ids:
            return error_response(400, "文章ID列表不能为空")

        from sqlalchemy import exists, or_

        from core.models.article import Article
        from core.models.article_tags import ArticleTag
        from core.models.tags import Tags
        from core.models.base import DATA_STATUS

        session = DB.get_session()
        try:
            # 支持传入 ["__all__"] 表示全量提取
            if request.article_ids == ["__all__"]:
                all_ids = session.query(Article.id).filter(
                    Article.status != DATA_STATUS.DELETED
                ).all()
                article_ids = [str(row.id) for row in all_ids]
            elif request.article_ids == ["__missing__"]:
                # 无任何 article_tags 行的文章（与 scripts/backfill_missing_article_tags 一致）
                no_tag_row = ~exists().where(ArticleTag.article_id == Article.id)
                rows = (
                    session.query(Article.id)
                    .filter(no_tag_row)
                    .filter(
                        or_(
                            Article.status != DATA_STATUS.DELETED,
                            Article.status.is_(None),
                            Article.status == 0,
                        ),
                        Article.title.isnot(None),
                        Article.title != "",
                    )
                    .all()
                )
                article_ids = [str(row.id) for row in rows]
            else:
                article_ids = request.article_ids

            success_count = 0
            error_count = 0
            results = []

            for article_id in article_ids:
                try:
                    article = session.query(Article).filter(Article.id == article_id).first()
                    if not article:
                        error_count += 1
                        results.append({"article_id": article_id, "error": "文章不存在"})
                        continue

                    if not article.title:
                        error_count += 1
                        results.append({"article_id": article_id, "error": "文章标题为空"})
                        continue

                    # 删除旧标签关联
                    old_tags = session.query(ArticleTag).filter(
                        ArticleTag.article_id == article_id
                    ).all()
                    for old_tag in old_tags:
                        session.delete(old_tag)
                    session.flush()

                    # 重新提取标签
                    content = article.content if hasattr(article, 'content') and article.content else ""
                    description = article.description if article.description else ""
                    
                    # 尝试重新提取
                    try:
                        DB._assign_tags_by_extraction(
                            session=session,
                            article_id=article_id,
                            title=article.title,
                            description=description,
                            content=content
                        )
                        # 显式 Commit 确保入库
                        session.commit()
                    except Exception as ext_e:
                        session.rollback()
                        print_error(f"提取过程报错: {ext_e}")

                    # 获取新标签名称用于返回
                    tag_names = []
                    new_article_tags = session.query(ArticleTag).filter(ArticleTag.article_id == article_id).all()
                    if new_article_tags:
                        t_ids = [at.tag_id for at in new_article_tags]
                        tags_objs = session.query(Tags).filter(Tags.id.in_(t_ids)).all()
                        tag_names = [t.name for t in tags_objs]

                    success_count += 1
                    results.append({
                        "article_id": article_id,
                        "title": article.title[:50],
                        "tags": tag_names
                    })
                except Exception as e:
                    session.rollback()
                    error_count += 1
                    results.append({"article_id": article_id, "error": str(e)})
                    from core.print import print_error
                    print_error(f"重新提取标签失败 [文章ID: {article_id}]: {e}")

            return success_response({
                "success_count": success_count,
                "error_count": error_count,
                "results": results
            }, message=f"成功处理 {success_count} 篇文章，失败 {error_count} 篇")
        finally:
            session.close()

    except Exception as e:
        from core.print import print_error
        print_error(f"批量重新提取标签失败: {e}")
        import traceback
        traceback.print_exc()
        return error_response(500, f"批量重新提取标签失败: {str(e)}")


@router.post("/extract_tags_missing/start", summary="启动补充缺失标签（异步，可轮询进度）")
async def start_extract_tags_missing(current_user: dict = Depends(get_current_user)):
    """仅处理「尚无任何标签」的文章；与 POST /extract_tags 中 __missing__ 逻辑一致，但不阻塞 HTTP。"""
    try:
        article_ids = _query_missing_tag_article_ids()
        total = len(article_ids)
        if total == 0:
            return success_response({"job_id": None, "total": 0}, message="没有待补充标签的文章")

        job_id = str(uuid.uuid4())
        with _MISSING_TAG_JOBS_LOCK:
            _MISSING_TAG_JOBS[job_id] = {
                "status": "running",
                "total": total,
                "processed": 0,
                "success_count": 0,
                "error_count": 0,
                "started_at": time.time(),
                "finished_at": None,
                "message": "处理中…",
            }

        threading.Thread(
            target=_missing_tags_worker,
            args=(job_id, article_ids),
            daemon=True,
        ).start()

        return success_response({"job_id": job_id, "total": total}, message="任务已启动")
    except Exception as e:
        from core.print import print_error
        print_error(f"启动补充缺失标签失败: {e}")
        return error_response(500, str(e))


@router.get("/extract_tags_missing/status", summary="查询补充缺失标签任务进度")
async def extract_tags_missing_status(
    job_id: str = Query(..., description="start 接口返回的 job_id"),
    current_user: dict = Depends(get_current_user),
):
    with _MISSING_TAG_JOBS_LOCK:
        j = _MISSING_TAG_JOBS.get(job_id)
    if not j:
        return error_response(404, "任务不存在或已过期")
    elapsed = None
    if j.get("started_at"):
        end = j.get("finished_at") or time.time()
        elapsed = round(end - float(j["started_at"]), 1)
    payload = {"job_id": job_id, **j, "elapsed_seconds": elapsed}
    return success_response(payload)


class ExportArticlesRequest(BaseModel):
    """导出文章请求模型"""
    mp_id: str  # type: ignore
    doc_id: Optional[List[str]] = None
    page_size: int = 10
    page_count: int = 1
    add_title: bool = True
    remove_images: bool = True
    remove_links: bool = False
    export_md: bool = False
    export_docx: bool = False
    export_json: bool = False
    export_csv: bool = False
    export_pdf: bool = True
    zip_filename: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "mp_id": "MP_WXS_3892772220",
                "doc_id": [],
                "page_size": 10,
                "page_count": 1,
                "add_title": True,
                "remove_images": True,
                "remove_links": False,
                "export_md": False,
                "export_docx": False,
                "export_json": False,
                "export_csv": False,
                "export_pdf": True,
                "zip_filename": ""
            }
        }

class ExportArticlesResponse(BaseModel):
    """导出文章响应模型"""
    record_count: int
    export_path: str
    message: str

class ExportFileInfo(BaseModel):
    """导出文件信息模型"""
    filename: str
    size: int
    created_time: str
    modified_time: str

def _export_articles_worker(
    mp_id: str,
    doc_id: Optional[List[str]],  # 改为 List[str]，因为文章ID是字符串类型
    page_size: int,
    page_count: int,
    add_title: bool,
    remove_images: bool,
    remove_links: bool,
    export_md: bool,
    export_docx: bool,
    export_json: bool,
    export_csv: bool,
    export_pdf: bool,
    zip_filename: Optional[str]
):
    """
    导出文章的工作线程函数
    """
    try:
        # 构建调用参数，如果 doc_id 是 None 则不传递该参数（使用默认值）
        export_kwargs = {
            "mp_id": mp_id,
            "page_size": page_size,
            "page_count": page_count,
            "add_title": add_title,
            "remove_images": remove_images,
            "remove_links": remove_links,
            "export_md": export_md,
            "export_docx": export_docx,
            "export_json": export_json,
            "export_csv": export_csv,
            "export_pdf": export_pdf,
            "zip_filename": zip_filename
        }
        # 只有当 doc_id 不是 None 时才传递
        if doc_id is not None:
            export_kwargs["doc_id"] = doc_id
        
        result = export_md_to_doc(**export_kwargs)
        return result
    except Exception as e:
        from core.print import print_error
        import traceback
        print_error(f"导出任务执行失败: {str(e)}")
        print_error(f"错误详情:\n{traceback.format_exc()}")
        raise

@router.post("/export/articles", summary="导出文章")
async def export_articles(
    request: ExportArticlesRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    导出文章为多种格式（使用线程池异步处理）
    """
    try:
        # 验证参数
        # 如果 mp_id 是 None 或空字符串，且没有指定 doc_id，则报错
        # 如果有 doc_id（选中文章导出），允许 mp_id 为空（会在 export_md_to_doc 中处理）
        if (request.mp_id is None or (isinstance(request.mp_id, str) and not request.mp_id.strip())):
            if not request.doc_id or len(request.doc_id) == 0:
                return error_response(400, "公众号ID不能为空")
            # 如果有 doc_id，使用 "all" 作为目录名
            export_mp_id = "all"
        else:
            # 如果 mp_id 是空字符串，使用 "all" 作为目录名
            export_mp_id = request.mp_id.strip() if request.mp_id and request.mp_id.strip() else "all"
        
        # 验证至少选择一个导出格式
        if not any([request.export_md, request.export_docx, request.export_json, request.export_csv, request.export_pdf]):
            return error_response(400, "请至少选择一个导出格式")
        
        # 检查是否已有相同 mp_id 的导出任务正在运行
        for thread in threading.enumerate():
            if thread.name == f"export_articles_{export_mp_id}":
                return error_response(400, "该公众号的导出任务已在处理中，请勿重复点击")
                
        # 直接生成 zip_filename 并返回
        docx_path = f"./data/docs/{export_mp_id}/"
        if request.zip_filename:
            zip_file_path = f"{docx_path}{request.zip_filename}"
            if not zip_file_path.endswith('.zip'):
                zip_file_path += '.zip'
        else:
            zip_file_path = f"{docx_path}exported_articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        # 调试：打印接收到的参数
        print(f"导出请求参数 - mp_id: {request.mp_id}, export_mp_id: {export_mp_id}, doc_id: {request.doc_id}, doc_id类型: {type(request.doc_id)}")
        
        # 启动后台线程执行导出操作
        export_thread = threading.Thread(
            target=_export_articles_worker,
            args=(
                export_mp_id,
                request.doc_id,
                request.page_size,
                request.page_count,
                request.add_title,
                request.remove_images,
                request.remove_links,
                request.export_md,
                request.export_docx,
                request.export_json,
                request.export_csv,
                request.export_pdf,
                request.zip_filename
            ),
            name=f"export_articles_{export_mp_id}",
            daemon=True  # 设置为守护线程，主程序退出时自动结束
        )
        export_thread.start()
        
        return success_response({
            "export_path": zip_file_path,
            "message": "导出任务已启动，请稍后下载文件"
        })
            
    except ValueError as e:
        from core.print import print_error
        print_error(f"导出参数验证失败: {str(e)}")
        return error_response(400, str(e))
    except Exception as e:
        from core.print import print_error
        import traceback
        print_error(f"导出任务启动失败: {str(e)}")
        print_error(f"错误详情:\n{traceback.format_exc()}")
        return error_response(500, f"导出失败: {str(e)}")

@router.get("/export/download", summary="下载导出文件")
async def download_export_file(
    filename: str = Query(..., description="文件名"),
    mp_id: Optional[str] = Query(None, description="公众号ID"),
    delete_after_download: bool = Query(False, description="下载后删除文件"),
    # current_user: dict = Depends(get_current_user)
):
    """
    下载导出的文件
    """
    try:
        file_path = f"./data/docs/{mp_id}/{filename}"
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        def cleanup_file():
            """后台任务：删除临时文件"""
            try:
                if os.path.exists(file_path) and delete_after_download:
                    os.remove(file_path)
            except Exception:
                pass
        
        return FileResponse(
            path=file_path,
            filename=filename,
            background=BackgroundTask(cleanup_file)
        )
        
    except Exception as e:
        return error_response(500, f"下载失败: {str(e)}")

@router.get("/export/list", summary="获取导出文件列表", response_model=BaseResponse)
async def list_export_files(
    mp_id: Optional[str] = Query(None, description="公众号ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定公众号的导出文件列表
    """
    try:
        from .ver import API_VERSION
        safe_root = os.path.abspath(os.path.normpath("./data/docs"))
        # Ensure mp_id is not None or empty
       
        export_path = os.path.abspath(os.path.join(safe_root, mp_id or ""))
        # Validate that export_path is within safe_root
        if not export_path.startswith(safe_root):
            return success_response([])
        if not os.path.exists(export_path):
            return success_response([])
        # Check directory permissions
        if not os.access(export_path, os.R_OK):
            return error_response(403, "无权限访问该目录")
        files = []
        for root, _, filenames in os.walk(export_path):
            # Ensure root is also within safe_root, in case of symlinks or traversal
            root_norm = os.path.abspath(root)
            if not root_norm.startswith(safe_root):
                continue
            for filename in filenames:
                if filename.endswith('.zip'):
                    file_path = os.path.join(root, filename)
                    try:
                        file_stat = os.stat(file_path)
                        file_path = os.path.relpath(file_path, export_path)
                        files.append({
                        "filename": filename,
                        "size": file_stat.st_size,
                        "created_time": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                        "modified_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "path": file_path,
                        "download_url": f"{API_VERSION}/tools/export/download?mp_id={mp_id}&filename={file_path}"  # 下载链接
                    })
                    except PermissionError:
                        continue
               
        
        # 按修改时间倒序排列
        files.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return success_response(files)
        
    except Exception as e:
        return error_response(500, f"获取文件列表失败: {str(e)}")

# 删除文件请求模型
class DeleteFileRequest(BaseModel):
    """删除文件请求模型"""
    filename: str
    mp_id: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "exported_articles_20241021_143000.zip",
                "mp_id": "MP_WXS_3892772220"
            }
        }

@router.delete("/export/delete", summary="删除导出文件", response_model=BaseResponse)
async def delete_export_file(
    request: DeleteFileRequest = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    删除指定的导出文件
    """
    try:
        # 参数验证
        if not request.filename :
            return error_response(400, "文件名和公众号ID不能为空")
        
        # 构建文件路径并做路径归一化及安全检测
        base_path = os.path.realpath(f"./data/docs/{request.mp_id}/")
        unsafe_path = os.path.join(base_path, request.filename)
        safe_path = os.path.realpath(os.path.normpath(unsafe_path))
        
        # 安全检查：确保文件在指定目录内，防止路径遍历攻击
        if not safe_path.startswith(base_path):
            return error_response(403, "无权限删除该文件")
        
        # 只允许删除.zip文件
        if not request.filename.endswith('.zip'):
            return error_response(400, "只能删除.zip格式的导出文件")
        
        # 检查文件是否存在
        if not os.path.exists(safe_path):
            return error_response(404, "文件不存在")
        
        # 删除文件
        os.remove(safe_path)
        
        return success_response({
            "filename": request.filename,
            "message": "文件删除成功"
        })
        
    except PermissionError:
        return error_response(403, "没有权限删除该文件")
    except ValueError as e:
        return error_response(422, f"请求参数验证失败: {str(e)}")
    except Exception as e:
        return error_response(500, f"删除文件失败: {str(e)}")

# 兼容性接口：支持查询参数方式删除
@router.delete("/export/delete-by-query", summary="删除导出文件(查询参数)", response_model=BaseResponse)
async def delete_export_file_by_query(
    filename: str = Query(..., description="文件名"),
    mp_id: str = Query(..., description="公众号ID"),
    current_user: dict = Depends(get_current_user)
):
    """
    删除指定的导出文件（通过查询参数）
    """
    # 创建请求对象并调用主删除函数
    request = DeleteFileRequest(filename=filename, mp_id=mp_id)
    return await delete_export_file(request, current_user)