import os
import datetime
import google.generativeai as genai

# 1. 配置 Gemini API
# 建议在 GitHub Secrets 中设置 GEMINI_API_KEY
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-pro')

def generate_content():
    # 定义 AI 的角色和任务
    prompt = """
    你是一位资深的 AI 产品经理和专栏作家。
    请针对今天的日期，写一篇关于 'AI 行业趋势' 或 '产品设计深度思考' 的短博文。
    要求：
    1. 语言专业且有见地。
    2. 包含一个吸引人的标题。
    3. 使用 Markdown 格式。
    4. 字数在 600 字左右。
    """
    response = model.generate_content(prompt)
    return response.text

def create_hugo_post(content):
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    # 提取第一行作为标题并去除 Markdown 符号
    lines = content.strip().split('\n')
    title = lines[0].replace('# ', '').replace('**', '')
    body = '\n'.join(lines[1:])

    # 构建 Hugo Front Matter
    post_template = f"""---
title: "{title}"
date: {today}T09:00:00+08:00
draft: false
tags: ["AI", "AutoUpdate"]
categories: ["DailyInsight"]
---

{body}
"""
    
    # 确保路径存在
    os.makedirs("content/posts", exist_ok=True)
    file_name = f"content/posts/ai-insight-{today}.md"
    
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(post_template)
    print(f"文件已生成: {file_name}")

if __name__ == "__main__":
    if not api_key:
        print("错误: 请设置环境变量 GEMINI_API_KEY")
    else:
        blog_content = generate_content()
        create_hugo_post(blog_content)