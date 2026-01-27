import os
import datetime
from google import genai

# 1. 配置客户端：强制指定使用 v1 稳定版接口
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(
    api_key=api_key,
    http_options={'api_version': 'v1'} # 【核心改动】强制使用 v1
)

def generate_content():
    # 尝试 2026 年最常用的两个模型名称
    # 如果 gemini-1.5-flash 报错，可以尝试改成 gemini-2.0-flash
    model_id = "gemini-1.5-flash" 
    
    prompt = "你是一位资深产品经理，请写一篇 600 字左右的 AI 行业周报或深度产品思考。要求：Markdown 格式，第一行是标题。"
    
    try:
        # 调试信息：列出你当前 API Key 能用的所有模型（只会在报错时有帮助）
        # for m in client.models.list(): print(f"可用模型: {m.name}")

        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"调用 Gemini 出错: {e}")
        return None

def create_hugo_post(content):
    if not content: return
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 格式化内容，适配 Hugo
    post_template = f"""---
title: "AI 视角：{today} 行业思考"
date: {today}T09:00:00+08:00
draft: false
tags: ["AutoUpdate", "AI"]
---

{content}
"""
    
    os.makedirs("content/posts", exist_ok=True)
    file_path = f"content/posts/ai-{today}.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(post_template)
    print(f"成功生成文章: {file_path}")

if __name__ == "__main__":
    if api_key:
        create_hugo_post(generate_content())
    else:
        print("未检测到环境变量 GEMINI_API_KEY")