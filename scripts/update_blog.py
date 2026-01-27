import os
import datetime
from google import genai

# 1. 配置新的 Gemini 客户端
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

def generate_content():
    # 使用 2026 年主流的 gemini-1.5-flash 模型，速度更快且免费额度高
    model_id = "gemini-1.5-flash" 
    prompt = """
    你是一位资深的 AI 产品经理。请针对今天写一篇 600 字左右的深度思考博客。
    要求：Markdown 格式，第一行必须是标题（不带 #），后续是正文。
    """
    
    try:
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
    lines = content.strip().split('\n')
    title = lines[0].strip()
    body = '\n'.join(lines[1:])

    post_template = f"""---
title: "{title}"
date: {today}T09:00:00+08:00
draft: false
tags: ["AI", "Automated"]
---

{body}
"""
    
    os.makedirs("content/posts", exist_ok=True)
    file_name = f"content/posts/ai-post-{today}.md"
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(post_template)
    print(f"成功生成文章: {file_name}")

if __name__ == "__main__":
    if api_key:
        blog_content = generate_content()
        create_hugo_post(blog_content)
    else:
        print("未检测到 GEMINI_API_KEY")