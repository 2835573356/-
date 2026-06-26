"""
Excel 上传接口 — 调用影刀 RPA 流程处理并落库
POST /api/v1/upload          上传 Excel 文件，触发处理，返回结果
GET  /api/v1/upload/records  最近的上传记录列表
GET  /api/v1/upload/records/{id}  单条上传记录详情
DELETE /api/v1/upload/records/{id}  删除上传记录
"""
import logging
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.common import success_response, error_response
from app.api.deps import require_auth
from app.services.upload_service import UploadService

logger = logging.getLogger("bi-dashboard")

router = APIRouter(prefix="/api/v1/upload", tags=["文件上传"])

# 允许的 Excel 类型
ALLOWED_EXT = (".xlsx", ".xls", ".csv")


@router.post("", summary="上传 Excel 并触发影刀异步流程")
async def upload_excel(
    file: UploadFile = File(..., description="待处理的 Excel 文件"),
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    上传 Excel 文件 -> 影刀文件服务 -> 触发异步 RPA 流程 -> 立即返回（status=running）。
    前端拿到 record.id 后轮询 GET /upload/{id}/status 获取进度与最终结果。
    """
    filename = file.filename or "upload.xlsx"
    if not filename.lower().endswith(ALLOWED_EXT):
        return error_response(40000, f"仅支持 {', '.join(ALLOWED_EXT)} 格式")

    file_bytes = await file.read()
    if not file_bytes:
        return error_response(40000, "文件内容为空")

    record = UploadService.start(
        db,
        file_bytes=file_bytes,
        filename=filename,
        created_by=user.username,
    )

    if record.status == "failed":
        return error_response(50000, record.error or "上传失败")

    return success_response(record.to_dict(), "已开始处理")


@router.get("/{record_id}/status", summary="查询上传处理进度")
def upload_status(
    record_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """轮询一次流程进度（running/success/failed），由前端定时调用。"""
    record = UploadService.poll(db, record_id)
    if not record:
        return error_response(40400, f"记录不存在: id={record_id}")
    return success_response(record.to_dict())


@router.get("/records", summary="最近的上传记录")
def list_records(
    limit: int = 20,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取最近的上传处理记录列表"""
    return success_response(UploadService.list_records(db, limit=limit))


@router.get("/records/{record_id}", summary="上传记录详情")
def get_record(
    record_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取单条上传记录详情（含完整结果）"""
    record = UploadService.get_record(db, record_id)
    if not record:
        return error_response(40400, f"记录不存在: id={record_id}")
    return success_response(record.to_dict())


@router.delete("/records/{record_id}", summary="删除上传记录")
def delete_record(
    record_id: int,
    user: User = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """删除一条上传处理记录"""
    ok = UploadService.delete_record(db, record_id)
    if not ok:
        return error_response(40400, f"记录不存在: id={record_id}")
    return success_response(message="删除成功")
