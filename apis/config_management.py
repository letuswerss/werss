from fastapi import APIRouter, Depends, HTTPException,Body,Path,Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from core.models.config_management import ConfigManagement
from core.db  import DB
from core.auth import get_current_user
from .base import  success_response, error_response
from core.config import cfg
router = APIRouter(prefix="/configs", tags=["配置管理"])


@router.get("",summary="获取配置项列表")
def list_configs(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    # db=DB.get_session()
    """获取配置项列表"""
    try:
        # total = db.query(ConfigManagement).count()
        # configs = db.query(ConfigManagement).offset(offset).limit(limit).all()
        from core.yaml_db import YamlDB
        configs = YamlDB.store_config_to_list(cfg._config) 
        total=len(configs)
        return success_response(data={
            "list": configs,
            "page": {
                    "limit": limit,
                    "offset": offset
                },
                "total": total
        })
    except Exception as e:
        return error_response(code=500, message=str(e))

@router.get("/{config_key}", summary="获取单个配置项详情")
def get_config(
    config_key: str,
    current_user: dict = Depends(get_current_user)
):
    """获取单个配置项详情"""
    try:
        db = DB.get_session()
        # 先从数据库查找
        config = db.query(ConfigManagement).filter(ConfigManagement.config_key == config_key).first()
        if config:
            return success_response(data=config)
        
        # 如果数据库中没有，从 YAML 配置中查找
        from core.yaml_db import YamlDB
        configs = YamlDB.store_config_to_list(cfg._config)
        for cfg_item in configs:
            if cfg_item.config_key == config_key:
                return success_response(data=cfg_item)

        # store_config_to_list 只扁平化两层，点号路径更深时这里补读合并后的 cfg
        raw = cfg.get(config_key, None, silent=True)
        if raw is not None:
            return success_response(
                data=ConfigManagement(
                    config_key=config_key,
                    config_value=str(raw),
                    description="YAML 配置项",
                )
            )
        # 文档约定存在、但旧版 yaml 可能未写键；空串表示「用内置默认」，避免设置页无意义 404
        if config_key == "article_tag.ai_prompt":
            return success_response(
                data=ConfigManagement(
                    config_key=config_key,
                    config_value="",
                    description="AI 标签提取提示词（空则使用内置模板；可在本页保存写入数据库）",
                )
            )

        # 如果都找不到，返回 404
        raise HTTPException(status_code=404, detail="Config not found")
    except HTTPException:
        raise
    except Exception as e:
        return error_response(code=500, message=str(e))

class ConfigManagementCreate(BaseModel):
    config_key: str
    config_value: str
    description: Optional[str] = None

class ConfigManagementUpdate(BaseModel):
    config_value: Optional[str] = None
    description: Optional[str] = None

@router.post("", summary="创建配置项")
def create_config(
    config_data: ConfigManagementCreate = Body(...),
    current_user: dict = Depends(get_current_user)
):
    db=DB.get_session()
    """创建配置项"""
    try:
        # 检查config_key是否已存在
        existing_config = db.query(ConfigManagement).filter(ConfigManagement.config_key == config_data.config_key).first()
        if existing_config:
            raise HTTPException(status_code=400, detail="Config with this key already exists")
        
        db_config = ConfigManagement(
            config_key=config_data.config_key,
            config_value=config_data.config_value,
            description=config_data.description
        )
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        try:
            from core.config_overrides import invalidate_config_overrides_cache

            invalidate_config_overrides_cache()
        except Exception:
            pass
        return success_response(data=db_config)
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))

@router.put("/{config_key}", summary="更新配置项")
def update_config(
    config_key: str=Path(...,min_length=1),
    config_data: ConfigManagementUpdate = Body(...),
    current_user: dict = Depends(get_current_user)
):
    db=DB.get_session()
    """更新配置项（不存在则插入，便于首次在控制台保存 yaml 中已有键）"""
    try:
        db_config = db.query(ConfigManagement).filter(ConfigManagement.config_key == config_key).first()
        if not db_config:
            if config_data.config_value is None:
                raise HTTPException(
                    status_code=400,
                    detail="Config not found; provide config_value to create",
                )
            db_config = ConfigManagement(
                config_key=config_key,
                config_value=config_data.config_value,
                description=(config_data.description or "控制台编辑"),
            )
            db.add(db_config)
        else:
            if config_data.config_value is None and config_data.description is None:
                raise HTTPException(
                    status_code=400,
                    detail="At least one field (config_value or description) must be provided",
                )
            if config_data.config_value is not None:
                db_config.config_value = config_data.config_value
            if config_data.description is not None:
                db_config.description = config_data.description
        
        db.commit()
        db.refresh(db_config)
        try:
            from core.config_overrides import invalidate_config_overrides_cache

            invalidate_config_overrides_cache()
        except Exception:
            pass
        return success_response(data=db_config)
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return error_response(code=500, message=str(e))
    finally:
        db.close()

@router.delete("/{config_key}",summary="删除配置项")
def delete_config(
    config_key: str,
    current_user: dict = Depends(get_current_user)
):
    db=DB.get_session()
    """删除配置项"""
    try:
        db_config = db.query(ConfigManagement).filter(ConfigManagement.config_key == config_key).first()
        if not db_config:
            raise HTTPException(status_code=404, detail="Config not found")
        
        db.delete(db_config)
        db.commit()
        try:
            from core.config_overrides import invalidate_config_overrides_cache

            invalidate_config_overrides_cache()
        except Exception:
            pass
        return success_response(message="Config deleted successfully")
    except Exception as e:
        db.rollback()
        return error_response(code=500, message=str(e))