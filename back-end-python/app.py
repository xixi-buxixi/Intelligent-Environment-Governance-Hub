from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import json
import sys
import subprocess
import requests
import re
from pathlib import Path
from dotenv import load_dotenv

from src.config import Config
from src.document_processor import DocumentProcessor
from src.vectorstore import VectorStoreManager
from src.rag_chain import RAGChain
from src.services.assistant_service import AssistantService
from src.services.comprehensive_predictor import (
    ComprehensivePredictor,
    PredictValidationError,
    normalize_factors,
)

import logging
from datetime import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


"""
Flask API服务

文件位置: app.py（项目根目录）

启动方式：
    python app.py

接口：
    GET  /health         - 健康检查
    POST /api/chat       - 问答
    POST /api/chat/stream - 流式问答
    POST /api/rebuild    - 重建知识库
"""

load_dotenv()

app = Flask(__name__)
CORS(app)

# 全局变量
rag_chain = None
vectorstore_manager = None
assistant_service = None
air_quality_predictor = ComprehensivePredictor()
PREDICT_RESULT_DIR = Path(__file__).resolve().parent / "runtime" / "predict_models" / "results"
RESULT_FACTOR_LABELS = {
    "AQI": "AQI",
    "PM25": "PM2.5",
    "PM10": "PM10",
    "SO2": "SO2",
    "NO2": "NO2",
    "CO": "CO",
    "O3": "O3",
}

def init_rag():
    """初始化RAG组件和助手服务"""
    global rag_chain, vectorstore_manager, assistant_service

    # 检查向量数据库是否存在
    if not os.path.exists(Config.VECTOR_DB_PATH):
        raise RuntimeError(
            "向量数据库不存在，请先运行 python main.py build 构建知识库"
        )

    # 加载向量数据库
    vectorstore_manager = VectorStoreManager(
        persist_directory=Config.VECTOR_DB_PATH,
        api_key=Config.OPENAI_API_KEY,
        embedding_model=Config.EMBEDDING_MODEL
    )
    retriever = vectorstore_manager.get_retriever(top_k=Config.RETRIEVE_TOP_K)

    # 创建RAG链
    rag_chain = RAGChain(
        retriever=retriever,
        model_name=Config.LLM_MODEL,
        api_key=Config.OPENAI_API_KEY,
    )
    
    # 初始化助手服务（注入 rag_chain）
    assistant_service = AssistantService(rag_chain=rag_chain)
    
    print("RAG组件和助手服务初始化完成")

@app.route('/health', methods=['GET'])
def health():

    return jsonify({
        "status": "healthy",
        "model": Config.LLM_MODEL
    })

# 创建日志目录
os.makedirs(Config.LOG_DIR, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.path.join(Config.LOG_DIR, 'app.log')
)
logger = logging.getLogger(__name__)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    """
    问答接口（支持多模式）

    请求体：
        {
            "question": "你的问题",
            "mode": "rag" | "agent" | "hybrid" | "direct" (可选，默认为 rag)
        }

    响应：
        {
            "question": "问题",
            "mode": "使用的模式",
            "answer": "回答",
            "meta": { ... } (元数据，如来源、耗时等)
        }
    """
    start_time = datetime.now()
    data = request.json
    question = data.get('question', '')
    mode = data.get('mode', 'rag')

    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    try:
        # 使用助手服务处理请求
        result = assistant_service.ask(question, mode=mode)
        
        # 记录日志
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"问题: {question[:50]}... | 模式: {mode} | 耗时: {duration:.2f}秒")

        return jsonify({
            "question": question,
            "mode": result["mode"],
            "answer": result["answer"],
            "meta": result.get("meta", {})
        })
    except Exception as e:
        logger.error(f"处理请求失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    流式问答接口

    使用 Server-Sent Events (SSE) 实现流式输出
    """
    data = request.json
    question = data.get('question', '')

    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    def generate():
        try:
            for chunk in rag_chain.stream(question):
                yield f"data: {json.dumps({'content': chunk})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream'
    )


@app.route('/api/rebuild', methods=['POST'])
def rebuild_knowledge():
    """
    重建知识库接口

    响应：
        {
            "status": "success",
            "message": "知识库重建完成",
            "chunks": 100
        }
    """
    try:
        # 处理文档
        processor = DocumentProcessor(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )
        chunks = processor.process(Config.KNOWLEDGE_PATH)

        # 创建向量数据库
        global vectorstore_manager
        vectorstore_manager = VectorStoreManager(
            persist_directory=Config.VECTOR_DB_PATH,
            api_key=Config.OPENAI_API_KEY,
            embedding_model=Config.EMBEDDING_MODEL
        )
        vectorstore_manager.create_from_documents(chunks)

        # 重新初始化
        init_rag()

        return jsonify({
            "status": "success",
            "message": "知识库重建完成",
            "chunks": len(chunks)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/spider/fetch', methods=['POST'])
def trigger_spider_fetch():
    """
    触发外部爬虫脚本，并在完成后回调Java端。
    请求体示例：
    {
      "city": "宜春",
      "startDate": "2026-04-01",
      "endDate": "2026-04-19",
      "dataType": "AQI",
      "callbackUrl": "http://localhost:8080/api/data/crawl/notify",
      "dbUser": "root",
      "dbPassword": "200575",
      "dbName": "environment_hub"
    }
    """
    data = request.json or {}
    data_type = str(data.get("dataType", "AQI")).upper()
    source_code = str(data.get("sourceCode", "aqi_history")).lower()
    callback_url = data.get("callbackUrl")

    spider_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spider")

    source_script_map = {
        "aqi_history": os.path.join("aqi", "aqi_history_spider.py"),
        "weather_history": os.path.join("weather", "weather_history_spider.py"),
        "env_news": os.path.join("news", "env_news_spider.py"),
    }
    if source_code not in source_script_map:
        return jsonify({
            "status": "failed",
            "message": f"source not allowed: {source_code}. allowed: {','.join(source_script_map.keys())}"
        }), 400
    script_rel = source_script_map[source_code]

    script_path = os.path.join(spider_root, script_rel)
    if not os.path.exists(script_path):
        return jsonify({"status": "failed", "message": f"spider script not found: {script_path}"}), 400

    env = os.environ.copy()
    env["DB_HOST"] = "localhost"
    env["DB_PORT"] = str(data.get("dbPort", "3306"))
    env["DB_USER"] = str(data.get("dbUser", "root"))
    env["DB_PASSWORD"] = str(data.get("dbPassword", ""))
    env["DB_NAME"] = str(data.get("dbName", "environment_hub"))

    finished_at = datetime.now().isoformat(timespec='seconds')
    status = "success"
    message = "crawl finished"
    stdout_preview = ""

    try:
        result = subprocess.run(
            [
                sys.executable,
                script_path,
                "--city", str(data.get("city", "宜春")),
                "--start-date", str(data.get("startDate")),
                "--end-date", str(data.get("endDate")),
            ],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=60 * 30
        )
        finished_at = datetime.now().isoformat(timespec='seconds')
        stdout_preview = (result.stdout or "")[-1200:]
        if result.returncode != 0:
            status = "failed"
            message = f"spider exit code {result.returncode}: {(result.stderr or '')[-300:]}"
    except Exception as e:
        finished_at = datetime.now().isoformat(timespec='seconds')
        status = "failed"
        message = f"spider run error: {str(e)}"

    payload = {
        "status": status,
        "message": message,
        "finishedAt": finished_at,
        "sourceCode": source_code,
        "dataType": data_type,
        "city": data.get("city"),
        "startDate": data.get("startDate"),
        "endDate": data.get("endDate"),
        "stdoutPreview": stdout_preview
    }

    if callback_url:
        try:
            requests.post(callback_url, json=payload, timeout=10)
        except Exception as callback_error:
            payload["callbackError"] = str(callback_error)

    if status != "success":
        return jsonify(payload), 500
    return jsonify(payload)


@app.route('/api/predict/air-quality', methods=['POST'])
def predict_air_quality():
    data = request.json or {}
    city = str(data.get("city", "")).strip()
    factors = normalize_factors(data.get("factors"))

    if not city:
        return jsonify({"error": "city 不能为空"}), 400
    if not factors:
        return jsonify({"error": "factors 不能为空，且至少包含一个有效空气因子"}), 400

    try:
        result = air_quality_predictor.predict(city=city, factors=factors)
    except PredictValidationError as exc:
        return jsonify({"error": exc.message}), exc.status_code
    except Exception as exc:
        return jsonify({"error": f"预测失败: {exc}"}), 500

    return jsonify({
        "data": result
    })


def read_factor_result_file(factor: str):
    path = PREDICT_RESULT_DIR / f"{factor}_result.txt"
    if not path.exists():
        return None

    content = path.read_text(encoding="utf-8", errors="replace")
    label = RESULT_FACTOR_LABELS.get(factor, factor)
    escaped_label = re.escape(label)
    row_pattern = re.compile(
        rf"(\d{{4}}-\d{{2}}-\d{{2}})\s*\|\s*{escaped_label}\s*:\s*([-+]?\d+(?:\.\d+)?)",
        re.IGNORECASE,
    )
    rows = [
        {"date": date_text, "value": float(value_text)}
        for date_text, value_text in row_pattern.findall(content)
    ][-7:]

    accuracy_match = re.search(r"Model Accuracy:\s*([-+]?\d+(?:\.\d+)?)%?", content)
    prediction_time_match = re.search(r"Prediction Time:\s*([^\r\n]+)", content)
    return {
        "factor": factor,
        "fileName": path.name,
        "lastModified": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy": float(accuracy_match.group(1)) if accuracy_match else None,
        "predictionTime": prediction_time_match.group(1).strip() if prediction_time_match else "",
        "rows": rows,
    }


@app.route('/api/predict/air-quality/results', methods=['GET'])
def get_air_quality_result_files():
    city = str(request.args.get("city", "")).strip()
    factors = normalize_factors(request.args.get("factors"))

    if not city:
        return jsonify({"error": "city 不能为空"}), 400
    if not factors:
        return jsonify({"error": "factors 不能为空，且至少包含一个有效空气因子"}), 400

    factor_results = {}
    missing_factors = []
    for factor in factors:
        result = read_factor_result_file(factor)
        if not result or len(result["rows"]) == 0:
            missing_factors.append(factor)
            continue
        factor_results[factor] = result

    if not factor_results:
        return jsonify({"error": "未找到所选空气因子的预测结果文件，请先重新生成预测"}), 404

    all_dates = sorted({row["date"] for result in factor_results.values() for row in result["rows"]})
    predictions = []
    for date_text in all_dates:
        one_day = {"date": date_text}
        for factor, result in factor_results.items():
            matched = next((row for row in result["rows"] if row["date"] == date_text), None)
            if matched:
                value = matched["value"]
                one_day[factor] = round(value, 2) if factor == "CO" else round(value, 2)
        predictions.append(one_day)

    return jsonify({
        "data": {
            "city": city,
            "factors": list(factor_results.keys()),
            "requestedFactors": factors,
            "missingFactors": missing_factors,
            "horizonDays": len(predictions),
            "startDate": predictions[0]["date"] if predictions else "",
            "historyDaysUsed": 0,
            "source": "result-files",
            "resultFiles": [
                {
                    "factor": result["factor"],
                    "fileName": result["fileName"],
                    "lastModified": result["lastModified"],
                    "accuracy": result["accuracy"],
                    "predictionTime": result["predictionTime"],
                }
                for result in factor_results.values()
            ],
            "predictions": predictions,
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("  环境小助手 - Flask API服务")
    print("=" * 60)

    init_rag()

    print("\n服务启动中...")
    print(f"API地址: http://localhost:5001")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=True)
















