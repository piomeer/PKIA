import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

class GitHubTrendingClient:
    """
    负责与 GitHub Trending 页面进行网络交互。
    只负责把 HTML 下载下来，绝对不包含任何解析逻辑（BeautifulSoup 不在这里）。
    """
    BASE_URL = "https://github.com/trending"

    def __init__(self):
        # 伪装成真实的浏览器，防止被 GitHub 基础反爬拦截
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.timeout = 15  # 设置 15 秒超时，防止 Pipeline 卡死

    def fetch_html(self, language: Optional[str] = None, since: str = "daily") -> str:
        """
        获取指定语言和时间范围的 Trending 页面 HTML。
        
        :param language: 编程语言，例如 'python', 'javascript'。留空则为全站总榜。
        :param since: 时间范围，可选 'daily', 'weekly', 'monthly'。
        :return: 页面的纯 HTML 字符串。
        """
        url = f"{self.BASE_URL}/{language}" if language else self.BASE_URL
        params = {"since": since}

        logger.info(f"正在请求 GitHub Trending... URL: {url}, Params: {params}")
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                params=params, 
                timeout=self.timeout
            )
            response.raise_for_status() # 如果返回 4xx 或 5xx 会抛出异常
            
            logger.info("HTML 下载成功！")
            return response.text
            
        except requests.RequestException as e:
            logger.error(f"获取 GitHub Trending 失败: {str(e)}")
            raise RuntimeError(f"Failed to fetch GitHub Trending: {str(e)}")
