"""
Excel 上传服务 — 调用影刀 RPA 开放平台
流程：
  1) 上传文件到影刀文件服务，拿到 {filename, url}
  2) 用该文件信息触发 RPA 流程异步执行，拿到 runRecordId
  3) 轮询结果；成功后解析数据行 -> 写入 posts 表 -> 落库到 upload_records 表
"""
import logging
from datetime import date, datetime
from typing import Optional, Tuple, Any
import requests
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.config import settings
from app.models.upload_record import UploadRecord
from app.models.post import Post
from app.models.root_cause import RootCauseAnalysis
from app.models.insight import BusinessInsight
from app.models.risk_alert import RiskAlert
from app.services.analysis_service import AnalysisService
from app.utils.cache import cache

logger = logging.getLogger("bi-dashboard")


# 影刀流程返回的列名 -> Post 字段 的别名映射（尽量兼容中英文/不同叫法）
_FIELD_ALIASES = {
    "title": ["title", "标题", "帖子标题", "问题标题", "主题", "问题", "提问", "问题内容", "问题描述"],
    "content": ["content", "正文", "内容", "帖子内容", "描述", "详情"],
    "category": ["category", "分类", "问题分类", "类别", "类型", "归属类别", "所属类别", "归类"],
    "priority": ["priority", "优先级", "优先级别", "级别"],
    "sentiment": ["sentiment", "情绪", "情感", "舆情", "提问人的情绪", "用户情绪", "情绪倾向"],
    "view_count": ["view_count", "浏览量", "浏览数", "阅读量", "阅读数"],
    "reply_count": ["reply_count", "回复数", "回复量", "评论数"],
    "author_name": ["author_name", "发帖人", "作者", "用户", "发布人", "提问人", "提问者"],
    "source": ["source", "来源", "渠道", "来源渠道"],
    "risk_level": ["risk_level", "风险等级", "风险级别", "风险"],
    "data_date": ["data_date", "日期", "数据日期", "发帖日期", "发布日期", "时间"],
}

# 情绪中文 -> 英文枚举
_SENTIMENT_MAP = {
    "消极": "negative", "负面": "negative", "negative": "negative",
    "中性": "neutral", "中立": "neutral", "neutral": "neutral",
    "积极": "positive", "正面": "positive", "positive": "positive",
}


def _classify_priority(view_count: int, category: str) -> str:
    """Keep uploaded rows aligned with dashboard priority semantics."""
    if category == "紧急求助":
        return "P0"
    if category == "功能咨询":
        return "P2"
    if category in {"Bug / 系统异常", "RPA执行问题", "Excel数据问题", "第三方系统问题"}:
        return "P0" if view_count >= 250 else "P1"
    return "P2"


class UploadService:
    """影刀 Excel 上传 + 流程执行服务"""

    @staticmethod
    def _mark_processing(record: UploadRecord, message: str) -> None:
        """Keep a transient/unconfirmed upload visible as processing instead of failed."""
        record.status = "running"
        record.error = message[:2000] if message else None

    @staticmethod
    def _yingdao_upload(file_bytes: bytes, filename: str) -> dict:
        """步骤 1：上传文件到影刀文件服务，返回 {filename, url}"""
        headers = {"Authorization": f"Bearer {settings.YINGDAO_TOKEN}"}
        files = {"file": (filename, file_bytes)}
        resp = requests.post(
            settings.YINGDAO_UPLOAD_URL,
            headers=headers,
            files=files,
            timeout=settings.YINGDAO_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()
        logger.info(f"[Upload] 文件上传响应: {body}")

        # 兼容多种返回结构，尽量取出 filename / url
        data = body.get("data", body) if isinstance(body, dict) else {}
        if not isinstance(data, dict):
            data = {}
        file_url = (
            data.get("fileReadUrl")
            or data.get("url")
            or data.get("fileUrl")
            or data.get("downloadUrl")
            or ""
        )
        ret_name = data.get("filename") or data.get("fileName") or data.get("name") or filename
        if not file_url:
            raise ValueError(f"影刀文件上传未返回 url，原始响应: {body}")
        return {"filename": ret_name, "url": file_url}

    @staticmethod
    def _yingdao_execute_async(filename: str, url: str) -> str:
        """步骤 2：触发 RPA 流程【异步】执行，返回 runRecordId（立即返回，不等流程跑完）"""
        headers = {
            "Authorization": f"Bearer {settings.YINGDAO_TOKEN}",
            "Content-Type": "application/json",
        }
        payload = {"input": {"uploaded_file": {"filename": filename, "url": url}}}
        resp = requests.post(
            settings.YINGDAO_FLOW_ASYNC_URL,
            headers=headers,
            json=payload,
            timeout=settings.YINGDAO_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()
        logger.info(f"[Upload] 异步流程触发响应: {str(body)[:500]}")
        data = body.get("data") if isinstance(body, dict) else None
        run_record_id = data.get("runRecordId") if isinstance(data, dict) else None
        if not run_record_id:
            msg = (body.get("msg") or body.get("message") or "") if isinstance(body, dict) else ""
            raise ValueError(f"影刀未返回 runRecordId: {msg or body}")
        return run_record_id

    @staticmethod
    def _yingdao_fetch_result(run_record_id: str) -> dict:
        """查询一次异步流程执行结果（不阻塞，由调用方轮询）"""
        headers = {
            "Authorization": f"Bearer {settings.YINGDAO_TOKEN}",
            "Content-Type": "application/json",
        }
        resp = requests.get(
            f"{settings.YINGDAO_RESULT_URL}?runRecordId={run_record_id}",
            headers=headers,
            timeout=settings.YINGDAO_TIMEOUT,
        )
        resp.raise_for_status()
        body = resp.json()
        logger.info(f"[Upload] 结果查询响应: {str(body)[:300]}")
        return body

    @staticmethod
    def _extract_status(node: Any) -> str:
        """Read execution status from common response field names."""
        if not isinstance(node, dict):
            return ""
        for key in ("status", "state", "runStatus", "executeStatus", "resultStatus"):
            value = node.get(key)
            if value:
                return str(value).lower()
        data = node.get("data")
        if isinstance(data, dict):
            return UploadService._extract_status(data)
        return ""

    @staticmethod
    def _extract_rows(result: Any) -> list:
        """
        尽力从流程结果里抽出一个"数据行数组"，用于前端表格展示与计数。
        影刀流程常把结果放在 output_text_0 等字段里，且值是 JSON 字符串，
        因此这里既递归找 list[dict]，也会尝试把字符串当 JSON 解析。
        """
        import json as _json

        def walk(node):
            if isinstance(node, str):
                s = node.strip()
                if s.startswith("[") or s.startswith("{"):
                    try:
                        return walk(_json.loads(s))
                    except Exception:
                        return None
                return None
            if isinstance(node, list):
                if node and all(isinstance(x, dict) for x in node):
                    return node
                for item in node:
                    found = walk(item)
                    if found:
                        return found
            elif isinstance(node, dict):
                # 优先看常见键
                for key in ("rows", "data", "result", "output", "list", "items", "records"):
                    if key in node:
                        found = walk(node[key])
                        if found:
                            return found
                for v in node.values():
                    found = walk(v)
                    if found:
                        return found
            return None

        rows = walk(result)
        return rows or []

    @staticmethod
    def _norm_key(k: str) -> str:
        return str(k).strip().lower().replace(" ", "").replace("　", "")

    @staticmethod
    def _map_row_to_post(row: dict) -> dict:
        """把一行（任意中英文列名）映射成 Post 可用的字段字典。"""
        # 构造 归一化key -> 原值
        norm = {UploadService._norm_key(k): v for k, v in row.items()}

        def pick(field):
            for alias in _FIELD_ALIASES.get(field, []):
                ak = UploadService._norm_key(alias)
                if ak in norm and norm[ak] not in (None, ""):
                    return norm[ak]
            return None

        title = pick("title")
        # 没有标题时，退而用内容/第一列，保证 NOT NULL
        if not title:
            content_val = pick("content")
            title = content_val or (next(iter(row.values()), None) if row else None)
        if not title:
            return {}  # 整行空，跳过

        # 情绪规整
        sentiment_raw = pick("sentiment")
        sentiment = _SENTIMENT_MAP.get(str(sentiment_raw).strip(), "neutral") if sentiment_raw else "neutral"

        # 日期规整
        data_date_val = pick("data_date")
        parsed_date = UploadService._parse_date(data_date_val) or date.today()

        def to_int(v):
            try:
                return int(float(v))
            except Exception:
                return 0

        view_count = to_int(pick("view_count"))
        category = str(pick("category") or "未分类")[:100]

        # 优先使用显式优先级；没有或非法时按分类严重性和浏览量推导。
        priority_raw = pick("priority")
        priority = str(priority_raw or "").upper().strip()
        if priority not in ("P0", "P1", "P2"):
            priority = _classify_priority(view_count, category)

        return {
            "title": str(title)[:500],
            "content": pick("content"),
            "category": category,
            "priority": priority,
            "sentiment": sentiment,
            "view_count": view_count,
            "reply_count": to_int(pick("reply_count")),
            "author_name": (str(pick("author_name"))[:100] if pick("author_name") else None),
            "source": (str(pick("source"))[:100] if pick("source") else "Excel导入"),
            "risk_level": (str(pick("risk_level"))[:20] if pick("risk_level") else None),
            "data_date": parsed_date,
        }

    @staticmethod
    def _parse_date(v) -> Optional[date]:
        if not v:
            return None
        if isinstance(v, date):
            return v
        s = str(v).strip()[:10].replace("/", "-")
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(s, fmt).date()
            except Exception:
                continue
        return None

    @staticmethod
    def _persist_posts(db: Session, rows: list) -> int:
        """把解析出的数据行写入 posts 表，返回成功写入条数。"""
        saved = 0
        affected_dates = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            mapped = UploadService._map_row_to_post(row)
            if not mapped:
                continue
            try:
                db.add(Post(**mapped))
                affected_dates.add(mapped["data_date"])
                saved += 1
            except Exception as e:
                logger.warning(f"[Upload] 跳过一行（构造 Post 失败）: {e}")
        if saved:
            db.commit()
            refreshed = UploadService._refresh_analysis_outputs(db, sorted(affected_dates))
            cache.delete_pattern("dashboard:*")  # 让看板刷新
            logger.info(f"[Upload] 已写入 posts 表 {saved} 条，刷新汇总日期: {refreshed}")
        return saved

    @staticmethod
    def _refresh_analysis_outputs(db: Session, dates: list) -> list:
        refreshed = []
        for dt in dates:
            try:
                summary = AnalysisService.generate_daily_summary(db, dt)
                if summary:
                    UploadService._generate_root_causes(db, dt)
                    UploadService._generate_insights(db, dt)
                    UploadService._generate_risk_alerts(db, dt)
                    refreshed.append(dt.isoformat())
            except Exception as e:
                logger.warning(f"[Upload] 刷新 {dt} 分析结果失败: {e}")
        return refreshed

    @staticmethod
    def _generate_root_causes(db: Session, dt: date) -> None:
        posts = db.query(Post).filter(Post.data_date == dt).all()
        total = len(posts)
        if not total:
            return

        db.query(RootCauseAnalysis).filter(RootCauseAnalysis.data_date == dt).delete()

        rows = db.query(
            Post.category,
            func.count(Post.id).label("count"),
        ).filter(Post.data_date == dt).group_by(Post.category).order_by(func.count(Post.id).desc()).limit(5).all()

        for index, (category, count) in enumerate(rows, 1):
            sample_titles = [
                p.title for p in posts
                if p.category == category and p.title
            ][:3]
            keywords = [category.replace("问题", "").replace(" / ", "/")]
            for title in sample_titles:
                if title and len(keywords) < 5:
                    keywords.append(str(title)[:12])

            db.add(RootCauseAnalysis(
                data_date=dt,
                cluster_name=f"{category}集中反馈",
                cluster_index=index,
                post_count=count,
                percentage=round(count / total * 100, 1),
                keywords=keywords,
                possible_cause=f"{category}相关问题在导入数据中出现较多，需要结合帖子详情确认共性。",
                suggestion="建议运营先归类高频帖子，产品/研发按优先级排查并同步处理进展。",
                priority_level="P0" if any(p.priority == "P0" for p in posts if p.category == category) else "P1",
            ))
        db.commit()

    @staticmethod
    def _generate_insights(db: Session, dt: date) -> None:
        posts = db.query(Post).filter(Post.data_date == dt).all()
        total = len(posts)
        if not total:
            return

        db.query(BusinessInsight).filter(BusinessInsight.data_date == dt).delete()

        p0_count = sum(1 for p in posts if p.priority == "P0")
        negative_count = sum(1 for p in posts if p.sentiment == "negative")
        top_category_row = db.query(
            Post.category,
            func.count(Post.id).label("count"),
        ).filter(Post.data_date == dt).group_by(Post.category).order_by(func.count(Post.id).desc()).first()
        top_category, top_count = top_category_row if top_category_row else ("未分类", 0)

        insights = [
            {
                "title": f"{top_category}为当前主要反馈来源",
                "impact": f"该分类共 {top_count} 条，占当日导入数据 {round(top_count / total * 100, 1)}%。",
                "suggestion": "优先查看该分类下的高浏览/高优先级帖子，提炼共性问题。",
                "severity": "high" if top_count / total >= 0.4 else "medium",
                "category": top_category,
            },
            {
                "title": f"P0/P1 问题共 {p0_count} 条 P0",
                "impact": "高优先级问题会直接影响风险中心和健康评分。",
                "suggestion": "建议对 P0 问题建立负责人和处理时限。",
                "severity": "critical" if p0_count >= 3 else ("high" if p0_count else "low"),
                "category": "priority",
            },
            {
                "title": f"消极情绪 {negative_count} 条",
                "impact": f"消极占比 {round(negative_count / total * 100, 1)}%，会影响社区健康度。",
                "suggestion": "优先回复消极反馈，并补充 FAQ 或临时解决方案。",
                "severity": "high" if negative_count / total >= 0.35 else "medium",
                "category": "sentiment",
            },
        ]

        for index, item in enumerate(insights, 1):
            db.add(BusinessInsight(
                data_date=dt,
                insight_index=index,
                **item,
            ))
        db.commit()

    @staticmethod
    def _generate_risk_alerts(db: Session, dt: date) -> None:
        posts = db.query(Post).filter(
            Post.data_date == dt,
            Post.priority.in_(("P0", "P1")),
        ).order_by(Post.priority, Post.view_count.desc(), Post.id.desc()).limit(10).all()

        db.query(RiskAlert).filter(RiskAlert.data_date == dt).delete()

        for post in posts:
            db.add(RiskAlert(
                data_date=dt,
                title=f"{post.priority}告警：{post.title[:80]}",
                priority=post.priority,
                description=f"{post.category} · {post.sentiment} · 浏览 {post.view_count}，建议跟进原帖处理。",
                view_count=post.view_count,
                is_systemic=post.category in {"Bug / 系统异常", "RPA执行问题", "Excel数据问题"},
                status="active",
            ))
        db.commit()

    @staticmethod
    def start(
        db: Session,
        file_bytes: bytes,
        filename: str,
        created_by: Optional[str] = None,
    ) -> UploadRecord:
        """
        启动一次上传：上传文件 -> 触发异步流程 -> 立即返回（status=running）。
        不等待流程跑完，避免长时间阻塞导致 Read timeout。后续由 poll() 查询进度。
        """
        record = UploadRecord(
            filename=filename,
            status="pending",
            created_by=created_by,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        try:
            uploaded = UploadService._yingdao_upload(file_bytes, filename)
            record.file_url = uploaded["url"]
            db.commit()

            run_record_id = UploadService._yingdao_execute_async(
                uploaded["filename"], uploaded["url"]
            )
            record.run_record_id = run_record_id
            record.status = "running"
            db.commit()
            db.refresh(record)
            logger.info(f"[Upload] 已触发异步流程 id={record.id}, runRecordId={run_record_id}")
        except Exception as e:
            db.rollback()
            record = db.query(UploadRecord).filter(UploadRecord.id == record.id).first()
            if record:
                UploadService._mark_processing(
                    record,
                    f"流程启动暂未确认，系统将继续保留处理中状态: {e}"
                )
                db.commit()
                db.refresh(record)
            logger.warning(f"[Upload] 启动暂未确认，保留 running: {e}")

        return record

    @staticmethod
    def poll(db: Session, record_id: int) -> Optional[UploadRecord]:
        """
        查询一次流程进度。若仍 running 则向影刀查一次结果：
          - 流程 success -> 解析行数、落库、置 success
          - 流程 failed  -> 记录错误、置 failed
          - 仍在跑       -> 保持 running
        已是终态(success/failed)的记录直接返回，不再请求影刀。
        """
        record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
        if not record:
            return None
        if record.status in ("success", "failed") or not record.run_record_id:
            return record

        try:
            body = UploadService._yingdao_fetch_result(record.run_record_id)
            data = body.get("data") if isinstance(body, dict) else None
            result = data if isinstance(data, dict) else body
            status_text = UploadService._extract_status(body)
            rows_preview = UploadService._extract_rows(result)
            has_output = bool(rows_preview)

            if status_text in ("success", "succeeded", "complete", "completed", "finish", "finished") or has_output:
                rows = rows_preview
                record.result = result
                record.row_count = len(rows)
                # 关键：把解析出的数据行写入 posts 表，更新到整个系统
                saved = UploadService._persist_posts(db, rows)
                record.saved_count = saved
                record.status = "success"
                logger.info(f"[Upload] 流程完成 id={record.id}, 解析 {record.row_count} 行, 入库 {saved} 条")
            elif status_text in ("failed", "fail", "error", "cancel", "cancelled"):
                record.result = data
                msg = (data or {}).get("msg") or (data or {}).get("message") or ""
                UploadService._mark_processing(
                    record,
                    f"影刀返回 {status_text}，暂不判定失败，继续等待人工确认或后续重试: {msg}"
                )
                logger.info(f"[Upload] 流程暂未成功 id={record.id}: {record.error}")
            # 其它状态(running/runnable/queue 等) 保持 running
            db.commit()
            db.refresh(record)
        except Exception as e:
            # 查询出错不立刻判失败，保持 running 让前端继续轮询
            logger.warning(f"[Upload] 轮询结果出错 id={record.id}: {e}")

        return record

    @staticmethod
    def list_records(db: Session, limit: int = 20) -> list:
        """最近的上传记录"""
        records = (
            db.query(UploadRecord)
            .order_by(UploadRecord.created_at.desc())
            .limit(limit)
            .all()
        )
        return [r.to_dict() for r in records]

    @staticmethod
    def get_record(db: Session, record_id: int) -> Optional[UploadRecord]:
        return db.query(UploadRecord).filter(UploadRecord.id == record_id).first()

    @staticmethod
    def delete_record(db: Session, record_id: int) -> bool:
        """删除一条上传记录，返回是否删除成功"""
        record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
        if not record:
            return False
        db.delete(record)
        db.commit()
        logger.info(f"[Upload] 已删除记录 id={record_id}")
        return True
