"""
高级工具实现（结构化参数）
"""

from langchain_core.tools import StructuredTool
from .schemas import EmailParams, RAGQAParams


def _send_email(params:EmailParams)->dict:
    """邮件发送实现"""
    # TODO: 接入真实邮件API
    return{
        "ok":True,
        "data": {
            "to": params.to,
            "subject": params.subject,
            "priority": params.priority,
        },
        "error": None,
    }

send_email_tool=StructuredTool.from_function(
    name="send_email",
    description="发送邮件。适用于需要给指定邮箱发送通知/报告的场景。",
    func=_send_email,
    args_schema=EmailParams,
)