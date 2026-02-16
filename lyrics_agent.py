import os
import time
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")

DEFAULT_ANALYSIS_MODEL = os.getenv("ANALYSIS_MODEL", "gemini-3-pro-preview")
DEFAULT_PROMPT_MODEL = os.getenv("PROMPT_MODEL", "gemini-3-flash-preview")
DEFAULT_IMAGE_MODEL = os.getenv("IMAGE_MODEL", "nano-banana-2-4k")
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT", "90"))
DEFAULT_IMAGE_MAX_RETRIES = int(os.getenv("IMAGE_MAX_RETRIES", "3"))
DEFAULT_IMAGE_DOWNLOAD_TIMEOUT = float(os.getenv("IMAGE_DOWNLOAD_TIMEOUT", "30"))

_client = None

def get_client():
    global _client
    if _client is None:
        if not API_KEY or not BASE_URL:
            raise RuntimeError("API_KEY or BASE_URL not found in .env file.")
        _client = OpenAI(
            api_key=API_KEY,
            base_url=BASE_URL,
            timeout=DEFAULT_TIMEOUT_SECONDS
        )
    return _client

def analyze_lyrics(raw_content, model=None):
    """
    Analyzes the lyrics/raw content using Gemini-3-Pro-Preview.
    Returns the analysis text formatted for Xiaohongshu + Metadata.
    """
    print("\n🎵 正在进行歌词深度赏析 (Gemini-3-Pro)...")
    client = get_client()
    
    system_prompt = """请你扮演一位资深的音乐评论家、文学教授兼小红书爆款文案创作者。
你的任务是对提供的歌词/歌曲信息进行深度的艺术风格分析，并输出一篇可以直接发布在小红书上的高质量笔记。

请遵循以下结构和要求：
1. **标题**：创作一个吸引人的标题，包含 Emoji。
2. **核心意象与画面感**：分析歌词构建的视觉场景和独特意象。
3. **修辞手法与语言炼字**：分析比喻、象征、遣词造句。
4. **情感基调**：描述传达的情绪。
5. **哲学/文化隐喻**：挖掘深层含义。
6. **一句话风格总结**：用极具文学性的一句话概括艺术高度。
7. **排版要求**：使用 Emoji (✨, 🎵, 📖, 🖋️ 等) 优化排版，使用列表和加粗突出重点，文风文艺、走心。
8. **Hashtags**：在文末添加 5-8 个相关的小红书话题标签。

写作风格约束（降低 AI 感）：
- 语气自然克制，像真实乐评人/小红书用户；避免夸饰堆叠与空泛套话。
- 避免“本文/作为/AI/模型”等元叙述。
- 多引用或贴近歌词原句（可短引），观点要落地，不要泛泛而谈。
- 句式有长有短，少用排比；控制篇幅在 300-500 字左右。
- Emoji 适量即可（3-6 个），不密集刷屏。

IMPORTANT: At the VERY END of your response, after the hashtags, you MUST output the extracted Song Name and Artist in the following strict format for the system to parse:

===METADATA===
Title: [Song Name]
Artist: [Artist Name]
"""

    user_content = f"""
请分析以下内容（其中包含歌名、歌手和歌词）：
\"\"\"
{raw_content}
\"\"\"
"""

    try:
        response = client.chat.completions.create(
            model=model or DEFAULT_ANALYSIS_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during analysis: {str(e)}"

def parse_analysis_response(full_response):
    parts = full_response.split("===METADATA===")
    xiaohongshu_post = parts[0].strip()
    metadata_part = parts[1].strip() if len(parts) > 1 else ""

    song_name = "Unknown_Song"
    artist = "Unknown_Artist"

    if metadata_part:
        for line in metadata_part.split('\n'):
            if "Title:" in line:
                song_name = line.split("Title:")[1].strip()
            elif "Artist:" in line:
                artist = line.split("Artist:")[1].strip()
    else:
        print("⚠️ 未能自动提取元数据，将使用默认文件名。")

    return xiaohongshu_post, song_name, artist

def generate_visual_prompt(song_name, artist, analysis_context, model=None):
    """
    Generates 3 Midjourney prompts for minimalist/texture backgrounds (Chinese output).
    """
    print(f"\n🎨 正在构思封面背景方案 (Gemini-3-Pro) for {song_name}...")
    client = get_client()

    system_prompt = """你是资深平面设计师，擅长极简主义、瑞士风格与抽象字体海报。目标是生成完整“歌曲卡片”（背景+排版文字），可直接用于社媒发布。

# 任务
根据提供的 Song Info 生成 3 条 Midjourney 歌曲卡片提示词，必须“干净、留白充分、适合承载文字”，并要求图像生成器在画面中渲染文字。
先判断歌曲受众（如：文艺/独立/校园/都市/治愈/二次元/复古等），再让风格和材质贴合该受众审美。
避免明显 AI 背景：画面要像“真实印刷或实体材质拍摄”的海报底图。

# 设计原则（Less is More）
1. **减少 AI 痕迹**：避免复杂插画、人脸、写实场景。
2. **强调质感**：使用 grainy / noise / paper texture / gradient / glass / light leak 等关键词。
3. **高设计感**：像高端美术馆海报或概念专辑封面。
4. **颜色**：单色 / 双色 / 低饱和，拒绝混乱色彩。
5. **画幅**：固定 --ar 3:4
6. **真实感约束**：加入 printmaking / screenprint / letterpress / scanned texture / film grain / lithograph 等关键词，避免“纯数字渲染感”。
7. **文字可读性**：确保文本区有稳定的明度对比（light background + dark type 或 dark background + light type），避免纹理穿过文字区域；指明“text area is clean, low-noise”；三种方案的主文字字号要偏大。

# 输出结构
[Texture/Material] + [Geometric/Abstract Element] + [Lighting/Mood] + [Color Palette] + [Style Keywords] + [Audience Cue] + [Card Layout Instructions] + [Typography Instructions] + --ar 3:4 --style raw --v 6.0

# 输出选项（必须生成 3 条）
Option A（The Material）：由你设计“高级感、艺术性、审美强”的歌词卡片方案，重点在材质触感与克制构图；避免生成大量背景元素，画面像可直接发布的成品卡片；配色方案必须克制且高级。
Option B（The Gradient）：柔和抽象渐变或光晕形态，纯氛围；避免复杂纹理与多余元素；配色克制高级；主文字字号偏大、文字区干净。
Option C（The Object）：空旷画面中一个极小、高对比符号物体；允许你自由发挥其符号与构图（仍需保持留白与高级克制）；配色克制高级；主文字字号偏大、文字区干净。

# 多语言
输出中文。如果需要放置歌词，请保留歌词的原语言。允许双语并排。

# 文字规则（由你决定内容多少）
你可以从“歌名/歌手/一句歌词/短副标题/版权声明”中选择要出现的文字数量与组合（可多可少），并在提示词里写出具体文字内容。
要求：说明字体风格、字号层级、对齐方式、留白区位置；确保可读性与高对比；主标题字体偏大（如占画面高度的 12-18%）。

# 输出格式
仅输出 3 行提示词（每行一条），不要解释、不要 Markdown、不要编号、不要多余文字。
"""

    user_content = f"""
Song Name: {song_name}
Artist: {artist}
Vibe: {analysis_context[:500]}... (derived from analysis)
Key Symbol: 从分析中提取或合理推断一个象征物（如果不确定，选择抽象几何元素）。
"""

    try:
        response = client.chat.completions.create(
            model=model or DEFAULT_PROMPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during prompt generation: {str(e)}"

def generate_image(prompt, filename, model=None, max_retries=None):
    """
    Generates an image using Nano-Banana-2-4k (Image Mode).
    Saves the image to the specified filename.
    """
    print(f"\n🖼️ 正在生成封面图片 (Nano-Banana-Image)...")
    print(f"📝 使用提示词: {prompt[:100]}...")
    client = get_client()

    if max_retries is None:
        max_retries = DEFAULT_IMAGE_MAX_RETRIES

    for attempt in range(1, max_retries + 1):
        try:
            response = client.images.generate(
                model=model or DEFAULT_IMAGE_MODEL,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )

            image_url = response.data[0].url
            print(f"🔗 图片 URL: {image_url}")

            # Download and save
            img_data = requests.get(
                image_url,
                timeout=DEFAULT_IMAGE_DOWNLOAD_TIMEOUT
            ).content
            with open(filename, 'wb') as handler:
                handler.write(img_data)

            print(f"✅ 图片已保存至: {filename}")
            return image_url
        except Exception as e:
            print(f"❌ 图片生成失败(第{attempt}次): {str(e)}")
            if attempt < max_retries:
                time.sleep(2 * attempt)
            else:
                return None

def _safe_filename(text):
    safe_name = "".join([c for c in text if c.isalpha() or c.isdigit() or c in (' ', '_')]).rstrip()
    return safe_name if safe_name else "cover_image"

def _split_prompts(raw_prompt):
    lines = [line.strip() for line in raw_prompt.splitlines() if line.strip()]
    return lines if lines else [raw_prompt.strip()]

def run_pipeline(raw_content, output_dir=None, analysis_model=None, prompt_model=None, image_model=None):
    # Step 1: Analysis & Metadata Extraction
    full_response = analyze_lyrics(raw_content, model=analysis_model)
    xiaohongshu_post, song_name, artist = parse_analysis_response(full_response)

    # Step 2: Prompt Generation
    visual_prompt = generate_visual_prompt(song_name, artist, xiaohongshu_post, model=prompt_model)

    # Step 3: Image Generation (3 variants)
    prompts = _split_prompts(visual_prompt)
    safe_name = _safe_filename(song_name)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    images = []
    for idx, prompt in enumerate(prompts[:3], start=1):
        suffix = chr(ord("A") + idx - 1)
        filename = f"{safe_name}_cover_{suffix}.png"
        if output_dir:
            filename = os.path.join(output_dir, filename)
        image_url = generate_image(prompt, filename, model=image_model)
        images.append({
            "prompt": prompt,
            "filename": filename,
            "image_url": image_url
        })

    return {
        "xiaohongshu_post": xiaohongshu_post,
        "song_name": song_name,
        "artist": artist,
        "visual_prompt": visual_prompt,
        "images": images
    }

def main():
    print("=== 小红书歌词赏析智能体 (Auto-Mode) ===")
    print("请直接粘贴包含歌名、歌手、歌词的完整内容 (输入 'END' 结束):")

    try:
        get_client()
    except RuntimeError as e:
        print(f"Error: {str(e)}")
        return
    
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == 'END':
            break
        lines.append(line)
    
    raw_content = "\n".join(lines)
    
    if not raw_content:
        print("未输入内容，程序退出。")
        return

    result = run_pipeline(raw_content)

    print("\n" + "="*20 + " [小红书文案] " + "="*20)
    print(result["xiaohongshu_post"])
    print("="*50)
    
    print(f"\n📋 识别信息: 歌名 [{result['song_name']}], 歌手 [{result['artist']}]")
    print(f"\n🎨 生成的生图提示词: {result['visual_prompt']}")

    print("\n✨ 任务全部完成！请查看生成的小红书文案与封面图。")

if __name__ == "__main__":
    main()
