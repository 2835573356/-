"""
WebSocket 接口 — 对应需求文档 4.2.10
WS /api/v1/ws/dashboard  看板实时数据推送
"""
import json
import asyncio
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.security import decode_access_token

logger = logging.getLogger("bi-dashboard.websocket")

router = APIRouter()


class ConnectionManager:
    """WebSocket 连接管理器"""

    def __init__(self):
        # token -> websocket 映射
        self.active_connections: dict = {}

    async def connect(self, websocket: WebSocket, token: str):
        await websocket.accept()
        self.active_connections[token] = websocket
        logger.info(f"WebSocket 连接建立: token={token[:10]}... (活跃: {len(self.active_connections)})")

    def disconnect(self, token: str):
        if token in self.active_connections:
            del self.active_connections[token]
            logger.info(f"WebSocket 断开: token={token[:10]}... (活跃: {len(self.active_connections)})")

    async def send_personal_message(self, message: dict, token: str):
        """向单个客户端发送消息"""
        websocket = self.active_connections.get(token)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(token)

    async def broadcast(self, message: dict):
        """向所有连接的客户端广播消息"""
        disconnected = []
        for token, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(token)

        for token in disconnected:
            self.disconnect(token)

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/api/v1/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket 连接端点
    客户端连接时需要提供 JWT token 作为查询参数

    服务端推送消息类型:
    - health_update: 健康度评分变化
    - new_alert: 新告警通知
    - data_refresh: 数据刷新通知
    - heartbeat: 心跳
    """
    # 验证 token
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="无效的认证令牌")
        return

    username = payload.get("sub", "unknown")

    try:
        await manager.connect(websocket, token)

        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "已连接到看板实时数据通道",
                "username": username,
                "timestamp": asyncio.get_event_loop().time(),
            }
        })

        # 维持连接并处理心跳
        while True:
            try:
                # 等待客户端消息 (ping/pong)
                data = await asyncio.wait_for(
                    websocket.receive_text(), timeout=30
                )
                msg = json.loads(data)

                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})

            except asyncio.TimeoutError:
                # 发送心跳
                try:
                    await websocket.send_json({
                        "type": "heartbeat",
                        "data": {"timestamp": asyncio.get_event_loop().time()}
                    })
                except Exception:
                    break

    except WebSocketDisconnect:
        logger.info(f"客户端主动断开: {username}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        manager.disconnect(token)


def _run_async_in_background(coro):
    """在后台安全地运行异步协程（兼容同步调用场景）"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        # 没有运行中的事件循环（如定时任务线程），在新线程中运行
        import threading
        def _run():
            new_loop = asyncio.new_event_loop()
            try:
                new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        t = threading.Thread(target=_run, daemon=True)
        t.start()


def notify_health_update(health_score: int, health_status: str):
    """通知所有客户端健康度变化（由定时任务调用）"""
    _run_async_in_background(
        manager.broadcast({
            "type": "health_update",
            "data": {
                "health_score": health_score,
                "health_status": health_status,
            }
        })
    )


def notify_new_alert(alert_data: dict):
    """通知所有客户端新告警"""
    _run_async_in_background(
        manager.broadcast({
            "type": "new_alert",
            "data": alert_data,
        })
    )


def notify_data_refresh():
    """通知所有客户端数据已刷新"""
    import time
    _run_async_in_background(
        manager.broadcast({
            "type": "data_refresh",
            "data": {
                "message": "数据已刷新",
                "timestamp": time.time(),
            }
        })
    )
