import json
import logging
import uuid
from datetime import datetime, timezone
from .github_client import GitHubTrendingClient
from .parser import GitHubTrendingParser

# 配置基础日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PKIACollector:
    """
    第一阶段：本地采集与验证控制器
    负责调度网络请求与解析，并将结果输出为本地 JSON 文件供核验。
    """
    def __init__(self):
        self.client = GitHubTrendingClient()
        self.parser = GitHubTrendingParser()

    def run(self, language: str = None, since: str = "daily", output_file: str = "test_projects.json"):
        # 生成全局唯一的批次号
        batch_id = f"BATCH-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4]}"
        logger.info(f"🚀 开始采集批次: {batch_id}")

        try:
            # 1. 抓取 HTML
            html_content = self.client.fetch_html(language=language, since=since)

            # 2. 解析 HTML 得到 ProjectRaw 列表
            projects = self.parser.parse(html_content=html_content, batch_id=batch_id)

            if not projects:
                logger.warning("⚠️ 警告：解析结果为空，请检查网络或 HTML 结构。")
                return []

            # 3. 落盘为本地 JSON 以供人工验证
            with open(output_file, "w", encoding="utf-8") as f:
                # 利用 Pydantic 的 model_dump 直接序列化
                json_data = [p.model_dump(mode='json') for p in projects]
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 采集与解析完成！共 {len(projects)} 个项目已保存至当前目录的 {output_file}")
            return projects

        except Exception as e:
            logger.error(f"❌ 采集任务失败: {str(e)}")
            return []

if __name__ == "__main__":
    collector = PKIACollector()
    # 测试抓取 Python 分类的全天热门榜单
    logger.info("=== 启动本地连通性测试 ===")
    collector.run(language="python", since="daily")
