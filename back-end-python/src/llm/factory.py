from typing import Optional
from src.config import Config


def get_chat_model(temperature: Optional[float] = None):
    provider=Config.LLM_PROVIDER.lower()
    if temperature is None:
        temperature = Config.LLM_TEMPERATURE

    # 默认走 OpenAI 兼容模式（DashScope compatible-mode），稳定性更高
    if provider in ("tongyi", "openai_compat"):
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=Config.LLM_MODEL,
                temperature=temperature,
                api_key=Config.OPENAI_API_KEY,
                base_url=Config.OPENAI_API_BASE,
            )

    # 如需走 Tongyi 原生 SDK，可显式设置 LLM_PROVIDER=tongyi_native
    if provider=="tongyi_native":
        from langchain_community.chat_models.tongyi import ChatTongyi
        return ChatTongyi(
            model_name=Config.LLM_MODEL,
            temperature=temperature,
            dashscope_api_key=Config.OPENAI_API_KEY,
        )

    raise ValueError(f"Unsupported LLM_PROVIDER: {Config.LLM_PROVIDER}")








