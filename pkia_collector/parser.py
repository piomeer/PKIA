import logging
from typing import List
from bs4 import BeautifulSoup
from .models import ProjectRaw

logger = logging.getLogger(__name__)

class GitHubTrendingParser:
    """
    纯粹的 HTML 解析器。
    将 GitHub Trending 的 HTML 转化为标准化的 ProjectRaw 胖对象列表。
    """
    def __init__(self):
        pass

    def parse(self, html_content: str, batch_id: str) -> List[ProjectRaw]:
        soup = BeautifulSoup(html_content, "html.parser")
        projects = []
        
        # GitHub Trending 的每个项目通常包在 <article class="Box-row"> 中
        articles = soup.find_all("article", class_="Box-row")
        
        if not articles:
            logger.warning("未能在 HTML 中找到任何项目 (Box-row)，请检查 HTML 内容或 GitHub DOM 是否发生变化。")
            return projects

        for article in articles:
            try:
                # 1. 提取 Repo URL, Owner 和 Project Name
                h2 = article.find("h2", class_="h3 lh-condensed")
                a_tag = h2.find("a") if h2 else None
                if not a_tag:
                    continue
                    
                repo_path = a_tag.get("href", "").strip("/") # 类似 "microsoft/markitdown"
                if not repo_path or "/" not in repo_path:
                    continue
                    
                owner, project_name = repo_path.split("/", 1)
                repo_url = f"https://github.com/{repo_path}"
                
                # 使用确定性 ID 防重
                project_id = f"PKIA-GH-{owner}-{project_name}"

                # 2. 提取简介 (Description)
                p_desc = article.find("p", class_="col-9")
                description = p_desc.get_text(strip=True) if p_desc else ""

                # 3. 提取语言 (Language)
                span_lang = article.find("span", itemprop="programmingLanguage")
                language = span_lang.get_text(strip=True) if span_lang else None

                # 4. 提取历史 Stars 和 Forks
                muted_links = article.find_all("a", class_="Link--muted")
                stars, forks = 0, 0
                if len(muted_links) >= 2:
                    stars_text = muted_links[0].get_text(strip=True).replace(",", "")
                    forks_text = muted_links[1].get_text(strip=True).replace(",", "")
                    stars = int(stars_text) if stars_text.isdigit() else 0
                    forks = int(forks_text) if forks_text.isdigit() else 0

                # 5. 提取今日新增 Stars
                today_stars = 0
                span_today = article.find("span", class_="float-sm-right")
                if span_today:
                    today_text = span_today.get_text(strip=True)
                    num_str = ''.join(filter(str.isdigit, today_text))
                    today_stars = int(num_str) if num_str else 0

                # 6. 组装 ProjectRaw 契约对象
                project = ProjectRaw(
                    project_id=project_id,
                    owner=owner,
                    project_name=project_name,
                    description=description,
                    language=language,
                    stars=stars,
                    forks=forks,
                    today_stars=today_stars,
                    repo_url=repo_url,
                    source="github_trending",
                    batch_id=batch_id
                )
                projects.append(project)

            except Exception as e:
                # 单个项目脏数据不中断全局
                logger.warning(f"解析项目时出错 [{owner}/{project_name}]: {str(e)}")
                continue
                
        logger.info(f"成功解析出 {len(projects)} 个项目 (Batch ID: {batch_id})")
        return projects
