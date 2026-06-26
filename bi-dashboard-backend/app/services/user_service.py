"""
用户服务 — 用户认证、CRUD 操作
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.user import User
from app.core.security import hash_password, verify_password, create_access_token


class UserService:
    """用户管理服务"""

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[dict]:
        """验证用户并返回 token"""
        user = db.query(User).filter(User.username == username, User.is_active == True).first()
        if not user or not verify_password(password, user.password_hash):
            return None

        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()

        # 生成 token
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id, "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user.to_dict(),
        }

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据 ID 获取用户"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_all(db: Session, page: int = 1, page_size: int = 20) -> tuple:
        """获取用户列表（分页）"""
        query = db.query(User)
        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return [u.to_dict() for u in users], total

    @staticmethod
    def create(db: Session, username: str, password: str, role: str = "viewer",
               display_name: str = None, email: str = None) -> User:
        """创建用户"""
        user = User(
            username=username,
            password_hash=hash_password(password),
            role=role,
            display_name=display_name,
            email=email,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user_id: int, **kwargs) -> Optional[User]:
        """更新用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user_id: int) -> bool:
        """删除用户"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        db.delete(user)
        db.commit()
        return True
