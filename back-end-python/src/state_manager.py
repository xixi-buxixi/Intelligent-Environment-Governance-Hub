"""
Agent状态持久化管理
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class StateManager:
    """
    状态管理器

    功能：
    1. 保存Agent执行状态
    2. 恢复中断的执行
    3. 状态历史记录
    """

    def __init__(self,state_dir:str="./agent_states"):
        """
        初始化状态管理器

        Args:
            state_dir: 状态存储目录
        """

        self.state_dir=Path(state_dir)
        self.state_dir.mkdir(parents=True,exist_ok=True)

    def save_state(self,session_id:str,state:Dict[str,Any])->str:
        """
        保存状态

        Args:
            session_id: 会话ID
            state: 状态数据

        Returns:
            状态文件路径
        """
        timestamp=datetime.now().strftime("%Y%m%d_%H%M%S")
        filename=f"{session_id}_{timestamp}.json"
        filepath=self.state_dir/filename

        state["saved_at"]=timestamp
        state["session_id"]=session_id

        with open(filepath,"w",encoding="utf-8") as f:
            json.dump(state,f,ensure_ascii=False,indent=2)

        return str(filepath)


    def load_state(self,filepath:str)->Dict[str,Any]:
        """
        加载状态

        Args:
            filepath: 状态文件路径

        Returns:
            状态数据
        """
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_latest_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定会话的最新状态

        Args:
            session_id: 会话ID

        Returns:
            最新状态或None
        """
        files=list(self.state_dir.glob(f"{session_id}_*.json"))
        if not files:
            return None

            # 按时间戳排序，取最新的
        files.sort(reverse=True)
        return self.load_state(str(files[0]))

    def list_sessions(self)->List[str]:
        """
        列出所有会话ID

        Returns:
            会话ID列表
        """
        files=list(self.state_dir.glob("*.json"))
        sessions=set()
        for f in files:
            # 从文件名提取session_id
            parts = f.stem.split("_")
            if len(parts) >= 1:
                sessions.add(parts[0])
        return list(sessions)



























