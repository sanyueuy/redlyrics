# 小红书歌词赏析智能体 (Xiaohongshu Lyrics Agent)

这是一个全自动化的 AI 智能体，旨在为音乐爱好者和创作者生成高质量的小红书歌词赏析笔记及配套的电影感封面图。

## 功能特点

1.  **深度赏析 (Gemini-3-Pro)**: 扮演资深乐评人，生成包含意象分析、修辞解读、情感基调的小红书爆款文案。
2.  **自动排版**: 自动生成标题、Emoji、列表和 Hashtags。
3.  **视觉创作 (Gemini + Nano-Banana)**:
    - 自动构思符合“Dark Academia/王家卫”风格的封面提示词。
    - 智能提取歌名与金句，生成带排版加字指令的 Prompt。
4.  **一键生图**: 直接调用绘图模型生成并保存高清封面图。

## 使用方法

1.  配置 `.env` 文件中的 API 密钥。
2.  运行脚本：
    ```bash
    python lyrics_agent.py
    ```
3.  在提示符下粘贴完整的歌曲信息（包含歌名、歌手、歌词），输入 `END` 结束。
4.  程序将自动输出文案并保存封面图片（例如 `青花瓷_cover.png`）。

## Web UI

1.  安装依赖：
    ```bash
    pip install -r requirements.txt
    ```
2.  启动服务：
    ```bash
    python app.py
    ```
3.  打开浏览器访问：`http://127.0.0.1:5000`

## 依赖库

- openai
- python-dotenv
- requests

## 演示封面

![flos_cover 演示图](static/outputs/flos_cover.png)