import requests
from bs4 import BeautifulSoup
from datetime import datetime
from supabase import create_client, Client
import os

# 1. 初始化 Supabase 连接（从环境变量读取，避免硬编码）
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 2. 配置项（按需修改你的案例数据源）
TARGET_URL = "https://www.example.com/law-cases"  # 替换为真实案例源
CASE_SELECTOR = ".case-item"  # 案例列表CSS选择器
TITLE_SELECTOR = ".case-title"  # 案例标题选择器
CONTENT_SELECTOR = ".case-content"  # 案例内容选择器

# 3. AI 解析函数（占位符，后续可替换为免费API）
def generate_analysis(content: str) -> str:
    """生成案例解析，替换为豆包/讯飞星火免费API即可"""
    try:
        # 示例：返回占位符解析（后续替换为真实API）
        return f"【核心争议点】{content[:100]}...（AI生成解析）"
    except Exception as e:
        return "暂无法提供解析"

# 4. 案例类型识别
def get_case_type(title: str) -> str:
    if "离婚" in title or "婚姻" in title:
        return "婚姻"
    elif "房产" in title or "产权" in title:
        return "房产"
    elif "诈骗" in title or "盗窃" in title:
        return "刑事"
    else:
        return "其他"

# 5. 爬取并写入 Supabase
def crawl_and_save():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 爬取目标页面
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        print(f"爬取页面失败：{str(e)}")
        return

    # 解析案例并去重入库
    case_items = soup.select(CASE_SELECTOR)
    new_count = 0
    for item in case_items:
        try:
            # 提取基础信息
            title = item.select_one(TITLE_SELECTOR).text.strip() if item.select_one(TITLE_SELECTOR) else "无标题"
            content = item.select_one(CONTENT_SELECTOR).text.strip() if item.select_one(CONTENT_SELECTOR) else "无内容"

            # 去重：检查标题是否已存在
            existing = supabase.table("law_cases").select("id").eq("title", title).execute()
            if existing.data:
                continue

            # 生成解析和类型
            analysis = generate_analysis(content[:800])
            case_type = get_case_type(title)

            # 写入 Supabase
            data = {
                "title": title,
                "content": content[:1000],  # 截取内容，节省存储
                "analysis": analysis,
                "case_type": case_type,
                "crawl_time": datetime.now().isoformat()
            }
            supabase.table("law_cases").insert(data).execute()
            new_count += 1
        except Exception as e:
            print(f"解析单条案例失败：{str(e)}")
            continue

    print(f"爬取完成：新增 {new_count} 条案例，总计 {len(supabase.table('law_cases').select('id').execute().data)} 条")

if __name__ == "__main__":
    crawl_and_save()
