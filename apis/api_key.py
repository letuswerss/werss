from fastapi import APIRouter, Depends, HTTPException, status, Body, Path, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import secrets
import uuid
from core.auth import get_current_user
from core.db import DB
from core.models.api_key import ApiKey, ApiKeyLog
from core.models import User as DBUser
from .base import success_response, error_response

router = APIRouter(prefix="/api-keys", tags=["API Key 管理"])


# Pydantic models for request/response
class ApiKeyCreate(BaseModel):
    name: str
    permissions: Optional[str] = None  # JSON string
    is_active: Optional[bool] = None  # 允许前端传递，但创建时默认使用 True


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[str] = None
    is_active: Optional[bool] = None


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    user_id: str
    permissions: Optional[str]
    is_active: bool
    last_used_at: Optional[str]
    created_at: str
    updated_at: str
    key: Optional[str] = None  # 只在创建时返回


class ApiKeyLogResponse(BaseModel):
    id: str
    api_key_id: str
    endpoint: str
    method: str
    ip_address: Optional[str]
    user_agent: Optional[str]
    status_code: int
    created_at: str


def _generate_api_key() -> str:
    """生成 API Key"""
    random_part = secrets.token_urlsafe(32)
    return f"werss_{random_part}"


@router.post("", summary="创建 API Key")
async def create_api_key(
    api_key_data: ApiKeyCreate = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """创建新的 API Key"""
    session = DB.get_session()
    try:
        # 验证用户信息
        username = current_user.get("username")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_response(
                    code=40001,
                    message="无法获取用户信息"
                )
            )
        
        # 从数据库获取用户，确保用户存在并获取用户的 id
        user = session.query(DBUser).filter(DBUser.username == username).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="用户不存在"
                )
            )
        
        user_id = str(user.id)  # 使用用户的 id 而不是 username
        
        # 验证用户权限（只有管理员或用户自己可以创建）
        if current_user.get("role") != "admin" and api_key_data.name:
            # 非管理员只能为自己创建
            pass
        
        # 处理 permissions - 直接使用字符串，不再使用 JSON 数组
        permissions_value = api_key_data.permissions if api_key_data.permissions else None
        
        # 生成 API Key
        api_key_value = _generate_api_key()
        
        # 创建 API Key 记录
        # 如果前端传递了 is_active，使用前端值；否则默认为 True
        is_active_value = api_key_data.is_active if api_key_data.is_active is not None else True
        
        new_api_key = ApiKey(
            id=str(uuid.uuid4()),
            key=api_key_value,
            name=api_key_data.name,
            user_id=user_id,  # 使用用户的 id
            permissions=permissions_value,
            is_active=is_active_value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        session.add(new_api_key)
        session.commit()
        session.refresh(new_api_key)
        
        # 返回包含 key 的响应（只显示一次）
        return success_response(data={
            "id": new_api_key.id,
            "name": new_api_key.name,
            "key": new_api_key.key,  # 只在创建时返回
            "user_id": new_api_key.user_id,
            "permissions": new_api_key.permissions,
            "is_active": new_api_key.is_active,
            "created_at": new_api_key.created_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(new_api_key, "created_at", None) is not None else None,
            "updated_at": new_api_key.updated_at.strftime("%Y-%m-%d %H:%M:%S") if getattr(new_api_key, "updated_at", None) is not None else None,
        }, message="API Key 创建成功，请妥善保存")
        import traceback
        error_trace = traceback.format_exc()
        print(f"创建 API Key 错误: {str(e)}")
        print(f"错误堆栈: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50001,
                message=f"创建 API Key 失败: {str(e)}"
            )
        )
    finally:
        session.close()


@router.get("", summary="获取 API Key 列表")
async def get_api_keys(
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """获取当前用户的 API Key 列表"""
    session = DB.get_session()
    try:
        # 构建查询条件
        query = session.query(ApiKey)
        
        # 非管理员只能查看自己的 API Key
        # 需要先获取用户的 id
        if current_user["role"] != "admin":
            username = current_user.get("username")
            if username:
                user = session.query(DBUser).filter(DBUser.username == username).first()
                if user:
                    query = query.filter(ApiKey.user_id == str(user.id))
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        api_keys = query.order_by(ApiKey.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # 格式化返回数据（不包含 key 值）
        api_key_list = []
        for ak in api_keys:
            api_key_list.append({
                "id": ak.id,
                "name": ak.name,
                "user_id": ak.user_id,
                "permissions": ak.permissions,
                "is_active": ak.is_active,
                "last_used_at": ak.last_used_at.strftime("%Y-%m-%d %H:%M:%S") if ak.last_used_at else None,
                "created_at": ak.created_at.strftime("%Y-%m-%d %H:%M:%S") if ak.created_at else None,
                "updated_at": ak.updated_at.strftime("%Y-%m-%d %H:%M:%S") if ak.updated_at else None,
            })
        
        return success_response(data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": api_key_list
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50002,
                message=f"获取 API Key 列表失败: {str(e)}"
            )
        )
    finally:
        session.close()


@router.get("/{api_key_id}", summary="获取 API Key 详情")
async def get_api_key(
    api_key_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    """获取指定 API Key 的详情"""
    session = DB.get_session()
    try:
        api_key = session.query(ApiKey).filter(ApiKey.id == api_key_id).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="API Key 不存在"
                )
            )
        
        # 权限检查：非管理员只能查看自己的 API Key
        if current_user["role"] != "admin":
            # 获取当前用户的 ID
            current_user_id = None
            
            # 优先使用 original_user（如果存在），避免重复查询
            original_user = current_user.get("original_user")
            if original_user:
                # original_user 可能是数据库对象或 Pydantic 模型对象
                current_user_id = str(getattr(original_user, 'id', None)) if hasattr(original_user, 'id') else None
            
            # 如果 original_user 不存在或没有 id，通过 username 查询
            if not current_user_id:
                username = current_user.get("username")
                if username:
                    user = session.query(DBUser).filter(DBUser.username == username).first()
                    if user:
                        current_user_id = str(user.id) if user.id is not None else None
            
            if not current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无法验证用户身份"
                    )
                )
            
            # 确保类型一致：都转换为字符串进行比较
            api_key_user_id_str = str(api_key.user_id) if api_key.user_id is not None else None
            
            if not api_key_user_id_str or current_user_id != api_key_user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无权限访问此 API Key"
                    )
                )
        
        return success_response(data={
            "id": api_key.id,
            "name": api_key.name,
            "user_id": api_key.user_id,
            "permissions": api_key.permissions,
            "is_active": api_key.is_active,
            "last_used_at": api_key.last_used_at.strftime("%Y-%m-%d %H:%M:%S") if api_key.last_used_at else None,
            "created_at": api_key.created_at.strftime("%Y-%m-%d %H:%M:%S") if api_key.created_at else None,
            "updated_at": api_key.updated_at.strftime("%Y-%m-%d %H:%M:%S") if api_key.updated_at else None,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50003,
                message=f"获取 API Key 详情失败: {str(e)}"
            )
        )
    finally:
        session.close()


@router.put("/{api_key_id}", summary="更新 API Key")
async def update_api_key(
    api_key_id: str = Path(...),
    api_key_data: ApiKeyUpdate = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """更新 API Key（名称、权限、启用状态）"""
    session = DB.get_session()
    try:
        api_key = session.query(ApiKey).filter(ApiKey.id == api_key_id).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="API Key 不存在"
                )
            )
        
        # 权限检查：非管理员只能修改自己的 API Key
        if current_user["role"] != "admin":
            # 获取当前用户的 ID
            current_user_id = None
            
            # 优先使用 original_user（如果存在），避免重复查询
            original_user = current_user.get("original_user")
            if original_user:
                # original_user 可能是数据库对象或 Pydantic 模型对象
                current_user_id = str(getattr(original_user, 'id', None)) if hasattr(original_user, 'id') else None
            
            # 如果 original_user 不存在或没有 id，通过 username 查询
            if not current_user_id:
                username = current_user.get("username")
                if username:
                    user = session.query(DBUser).filter(DBUser.username == username).first()
                    if user:
                        current_user_id = str(user.id) if user.id is not None else None
            
            if not current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无法验证用户身份"
                    )
                )
            
            # 确保类型一致：都转换为字符串进行比较
            api_key_user_id_str = str(api_key.user_id) if api_key.user_id is not None else None
            
            if not api_key_user_id_str or current_user_id != api_key_user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无权限修改此 API Key"
                    )
                )
        
        # 更新字段
        if api_key_data.name is not None:
            api_key.name = api_key_data.name
        if api_key_data.permissions is not None:
            # 直接使用字符串，不再使用 JSON
            api_key.permissions = api_key_data.permissions if api_key_data.permissions else None
        if api_key_data.is_active is not None:
            api_key.is_active = api_key_data.is_active
        
        api_key.updated_at = datetime.now()
        session.commit()
        session.refresh(api_key)
        
        return success_response(data={
            "id": api_key.id,
            "name": api_key.name,
            "user_id": api_key.user_id,
            "permissions": api_key.permissions,
            "is_active": api_key.is_active,
            "last_used_at": api_key.last_used_at.strftime("%Y-%m-%d %H:%M:%S") if api_key.last_used_at else None,
            "created_at": api_key.created_at.strftime("%Y-%m-%d %H:%M:%S") if api_key.created_at else None,
            "updated_at": api_key.updated_at.strftime("%Y-%m-%d %H:%M:%S") if api_key.updated_at else None,
        }, message="更新成功")
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50004,
                message=f"更新 API Key 失败: {str(e)}"
            )
        )
    finally:
        session.close()


@router.delete("/{api_key_id}", summary="删除 API Key")
async def delete_api_key(
    api_key_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    """删除 API Key"""
    session = DB.get_session()
    try:
        api_key = session.query(ApiKey).filter(ApiKey.id == api_key_id).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="API Key 不存在"
                )
            )
        
        # 权限检查：非管理员只能删除自己的 API Key
        if current_user["role"] != "admin":
            # 优先使用 original_user（如果存在），避免重复查询
            user = current_user.get("original_user")
            if not user:
                username = current_user.get("username")
                if username:
                    user = session.query(DBUser).filter(DBUser.username == username).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无法验证用户身份"
                    )
                )
            
            # 确保类型一致：都转换为字符串进行比较
            user_id_str = str(user.id) if user.id is not None else None
            api_key_user_id_str = str(api_key.user_id) if api_key.user_id is not None else None
            
            if not user_id_str or not api_key_user_id_str or user_id_str != api_key_user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无权限删除此 API Key"
                    )
                )
        
        session.delete(api_key)
        session.commit()
        
        return success_response(message="删除成功")
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50005,
                message=f"删除 API Key 失败: {str(e)}"
            )
        )
    finally:
        session.close()


@router.get("/{api_key_id}/logs", summary="获取 API Key 使用日志")
async def get_api_key_logs(
    api_key_id: str = Path(...),
    current_user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """获取指定 API Key 的使用日志"""
    session = DB.get_session()
    try:
        # 检查 API Key 是否存在及权限
        api_key = session.query(ApiKey).filter(ApiKey.id == api_key_id).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="API Key 不存在"
                )
            )
        
        # 权限检查：非管理员只能查看自己的 API Key 日志
        if current_user["role"] != "admin":
            # 获取当前用户的 ID
            current_user_id = None
            
            # 优先使用 original_user（如果存在），避免重复查询
            original_user = current_user.get("original_user")
            if original_user:
                # original_user 可能是数据库对象或 Pydantic 模型对象
                original_user_id = getattr(original_user, 'id', None)
                current_user_id = str(original_user_id) if original_user_id is not None else None
            
            # 如果 original_user 不存在或没有 id，通过 username 查询
            if not current_user_id:
                username = current_user.get("username")
                if username:
                    user = session.query(DBUser).filter(DBUser.username == username).first()
                    if user:
                        current_user_id = str(user.id) if user.id is not None else None
            
            if not current_user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无法验证用户身份"
                    )
                )
            
            # 确保类型一致：都转换为字符串进行比较
            api_key_user_id_str = str(api_key.user_id) if api_key.user_id is not None else None
            
            if not api_key_user_id_str or current_user_id != api_key_user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无权限查看此 API Key 的日志"
                    )
                )
        
        # 查询日志
        query = session.query(ApiKeyLog).filter(ApiKeyLog.api_key_id == api_key_id)
        total = query.count()
        
        logs = query.order_by(ApiKeyLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # 格式化返回数据
        log_list = []
        for log in logs:
            log_list.append({
                "id": log.id,
                "api_key_id": log.api_key_id,
                "endpoint": log.endpoint,
                "method": log.method,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "status_code": log.status_code,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else None,
            })
        
        return success_response(data={
            "total": total,
            "page": page,
            "page_size": page_size,
            "list": log_list
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50006,
                message=f"获取使用日志失败: {str(e)}"
            )
        )
    finally:
        session.close()


@router.post("/{api_key_id}/regenerate", summary="重新生成 API Key")
async def regenerate_api_key(
    api_key_id: str = Path(...),
    current_user: dict = Depends(get_current_user)
):
    """重新生成 API Key（会生成新的 key 值）"""
    session = DB.get_session()
    try:
        api_key = session.query(ApiKey).filter(ApiKey.id == api_key_id).first()
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_response(
                    code=40401,
                    message="API Key 不存在"
                )
            )
        
        # 权限检查：非管理员只能重新生成自己的 API Key
        if current_user["role"] != "admin":
            # 优先使用 original_user（如果存在），避免重复查询
            user = current_user.get("original_user")
            if not user:
                username = current_user.get("username")
                if username:
                    user = session.query(DBUser).filter(DBUser.username == username).first()
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无法验证用户身份"
                    )
                )
            
            # 确保类型一致：都转换为字符串进行比较
            user_id_str = str(user.id) if user.id is not None else None
            api_key_user_id_str = str(api_key.user_id) if api_key.user_id is not None else None
            
            if not user_id_str or not api_key_user_id_str or user_id_str != api_key_user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=error_response(
                        code=40301,
                        message="无权限重新生成此 API Key"
                    )
                )
        
        # 生成新的 API Key
        new_key = _generate_api_key()
        api_key.key = new_key
        api_key.updated_at = datetime.now()
        session.commit()
        session.refresh(api_key)
        
        # 返回包含新 key 的响应（只显示一次）
        return success_response(data={
            "id": api_key.id,
            "name": api_key.name,
            "key": api_key.key,  # 只在重新生成时返回
            "user_id": api_key.user_id,
            "permissions": api_key.permissions,
            "is_active": api_key.is_active,
            "created_at": api_key.created_at.strftime("%Y-%m-%d %H:%M:%S") if api_key.created_at else None,
            "updated_at": api_key.updated_at.strftime("%Y-%m-%d %H:%M:%S") if api_key.updated_at else None,
        }, message="API Key 重新生成成功，请妥善保存")
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response(
                code=50007,
                message=f"重新生成 API Key 失败: {str(e)}"
            )
        )
    finally:
        session.close()



