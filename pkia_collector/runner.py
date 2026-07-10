import os
import sys
import logging
import requests
from dotenv import load_dotenv
from .collector import PKIACollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DifyRunner:
    """
    负责将 Collector 采集到的 Fat Object 数组，按照 Dify Workflow 的标准 Payload 格式推送。
    """
    def __init__(self, api_key: str, base_url: str = "http://127.0.0.1/v1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.collector = PKIACollector()

    def run_and_push(self, language: str = None, since: str = "daily"):
        # 1. 本地采集数据
        logger.info("=== 阶段 1: 启动数据采集 ===")
        projects = self.collector.run(language=language, since=since, output_file="latest_run.json")
        
        if not projects:
            logger.error("没有采集到任何项目，停止向 Dify 推送。")
            return

        # 2. 组装 Dify Payload
        # Dify Start Node 约定的入参变量名为 "projects"
        logger.info("=== 阶段 2: 组装 Dify Payload ===")
        projects_data = [p.model_dump(mode='json') for p in projects]
        
        payload = {
            "inputs": {
                "projects": projects_data
            },
            "response_mode": "blocking", # 阻塞等待工作流执行完毕
            "user": "pkia-auto-collector"
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 3. 发送 POST 请求触发 Dify
        url = f"{self.base_url}/workflows/run"
        logger.info(f"🚀 开始将 {len(projects_data)} 个项目推送到 Dify: {url}")

        try:
            # 设置 120 秒超时，因为大模型打分可能需要较长时间
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ 成功触发 Dify 工作流！工作流 ID: {result.get('workflow_run_id')}")
            logger.info(f"工作流最终状态: {result.get('data', {}).get('status')}")
            
        except requests.RequestException as e:
            logger.error(f"❌ 推送 Dify 失败: {str(e)}")
            if e.response is not None:
                logger.error(f"Dify 报错详情: {e.response.text}")

if __name__ == "__main__":
    load_dotenv()

    DIFY_API_KEY = os.getenv("DIFY_API_KEY")
    if not DIFY_API_KEY:
        logger.error("❌ 未找到 DIFY_API_KEY，请在 .env 文件中配置 DIFY_API_KEY=app-你的真实KEY")
        sys.exit(1)

    DIFY_API_URL = os.getenv("DIFY_API_URL", "http://127.0.0.1/v1")

    runner = DifyRunner(api_key=DIFY_API_KEY, base_url=DIFY_API_URL)

    runner.run_and_push(language="python", since="daily")
