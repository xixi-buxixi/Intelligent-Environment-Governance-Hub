import os
from typing import Dict
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT / '.env'

load_dotenv(DOTENV_PATH, override=False)


class DatabaseConfig:
    """统一数据库配置管理类"""

    DEFAULTS = {
        'host': 'localhost',
        'port': 3306,
        'user': '',
        'password': '',
        'database': 'environment_hub'
    }

    ENV_MAPPING = {
        'host': 'DB_HOST',
        'port': 'DB_PORT',
        'user': 'DB_USER',
        'password': 'DB_PASSWORD',
        'database': 'DB_NAME'
    }

    @classmethod
    def get_config(cls) -> Dict[str, str]:
        config = {}
        for key, env_var in cls.ENV_MAPPING.items():
            config[key] = os.getenv(env_var, str(cls.DEFAULTS[key]))
        return config

    @classmethod
    def get_database_uri(cls) -> str:
        config = cls.get_config()
        user = quote_plus(str(config['user']))
        password = quote_plus(str(config['password']))
        host = str(config['host'])
        port = str(config['port'])
        database = quote_plus(str(config['database']))
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"


db_config = DatabaseConfig.get_config()
DB_CONFIG = DatabaseConfig.get_config()
DATABASE_URI = DatabaseConfig.get_database_uri()


class Config:
    # ============ API配置 ============
    # 通义千问API（OpenAI兼容方式）
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # 不允许硬编码默认值
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    # ============ 模型配置 ============
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "tongyi")
    # 对话模型
    LLM_MODEL = os.getenv("LLM_MODEL", "qwen3.5-35b-a3b")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    # 嵌入模型
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

    # ============ Agent配置 ============
    AGENT_MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "6"))
    AGENT_MAX_RETRIES = int(os.getenv("AGENT_MAX_RETRIES", "3"))
    AGENT_MAX_HISTORY = int(os.getenv("AGENT_MAX_HISTORY", "10"))
    AGENT_ENABLE_REFLECTION = os.getenv("AGENT_ENABLE_REFLECTION", "true").lower() == "true"
    AGENT_STATE_DIR = os.getenv("AGENT_STATE_DIR", "./runtime/agent_states")

    VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./runtime/chroma_db")
    KNOWLEDGE_PATH = os.getenv("KNOWLEDGE_PATH", "./data/knowledge")
    LOG_DIR = os.getenv("LOG_DIR", "./runtime/logs")

    # ============ 文档处理配置 ============
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
    SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]

    # ============ 检索配置 ============
    RETRIEVE_TOP_K = 3  # 检索返回的文档数量
