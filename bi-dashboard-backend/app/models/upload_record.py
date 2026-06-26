"""
Excel 上传记录表模型 — 记录每次通过影刀 RPA 流程处理的上传文件及其返回结果
"""
from sqlalchemy import (
    Column, BigInteger, String, Text, Integer, DateTime, JSON
)
from sqlalchemy.sql import func
from app.database import Base


class UploadRecord(Base):
    __tablename__ = "upload_records"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    filename = Column(String(500), nullable=False, comment="上传的文件名")
    file_url = Column(Text, comment="影刀文件服务返回的文件 URL")
    run_record_id = Column(String(100), index=True, comment="影刀异步流程执行 ID")
    status = Column(String(20), nullable=False, default="pending", index=True, comment="处理状态: pending/running/success/failed")
    result = Column(JSON, comment="影刀流程返回的原始结果")
    row_count = Column(Integer, default=0, comment="解析出的数据条数")
    saved_count = Column(Integer, default=0, comment="实际写入 posts 表的条数")
    error = Column(Text, comment="失败原因")
    created_by = Column(String(100), comment="上传人")
    created_at = Column(DateTime, server_default=func.now(), comment="上传时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<UploadRecord(id={self.id}, filename='{self.filename}', status='{self.status}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "file_url": self.file_url,
            "run_record_id": self.run_record_id,
            "status": self.status,
            "result": self.result,
            "row_count": self.row_count,
            "saved_count": self.saved_count,
            "error": self.error,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
