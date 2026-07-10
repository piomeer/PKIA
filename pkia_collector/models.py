from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field

class ProjectRaw(BaseModel):
    """
    核心数据契约：GitHub 原始项目数据模型 (Fat Object)
    """
    project_id: str = Field(..., description="全局唯一主键，例如: f'PKIA-GH-{owner}-{project_name}'")
    owner: str = Field(..., description="项目作者或组织名称")
    project_name: str = Field(..., description="项目名称")
    repo_url: str = Field(..., description="项目完整 GitHub URL")
    
    description: str = Field(default="", description="项目原始简介")
    language: Optional[str] = Field(default=None, description="主要编程语言")
    topics: List[str] = Field(default_factory=list, description="项目标签/Topics")
    
    stars: int = Field(default=0, description="历史总 Star 数")
    forks: int = Field(default=0, description="历史总 Fork 数")
    today_stars: int = Field(default=0, description="今日新增 Star 数")
    
    source: str = Field(default="github_trending", description="数据采集来源")
    batch_id: str = Field(..., description="采集批次号")
    collection_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="数据采集时间 (UTC)"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
