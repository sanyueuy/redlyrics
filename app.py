import os
import uuid
from flask import Flask, render_template, request, redirect, url_for
from lyrics_agent import (
    analyze_lyrics,
    generate_visual_prompt,
    generate_image,
    parse_analysis_response,
    DEFAULT_ANALYSIS_MODEL,
    DEFAULT_PROMPT_MODEL,
    DEFAULT_IMAGE_MODEL,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(APP_DIR, "static", "outputs")
DISCLAIMER = "本段落中所使用的歌词，其著作权属于原著作权人，仅以介绍为目的引用。"

app = Flask(__name__)

STATE_STORE = {}

ANALYSIS_MODELS = [
    DEFAULT_ANALYSIS_MODEL,
    "gemini-3-pro-preview",
    "gemini-3-pro-preview-thinking-*",
    "gemini-3-flash-preview",
    "gemini-3-flash-preview-nothinking",
    "gemini-3-flash-preview-thinking-*",
    "gemini-2.5-pro",
    "gemini-2.0-pro",
]
PROMPT_MODELS = [
    DEFAULT_PROMPT_MODEL,
    "gemini-3-flash-preview",
    "gemini-3-flash-preview-nothinking",
    "gemini-3-flash-preview-thinking-*",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]
IMAGE_MODELS = [
    DEFAULT_IMAGE_MODEL,
    "nano-banana-2",
    "nano-banana-2-2k",
    "nano-banana-2-4k",
    "gemini-3-pro-image-preview",
]


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    raw_content = ""
    analysis_text = ""
    song_name = ""
    artist = ""
    prompt_a = ""
    prompt_b = ""
    prompt_c = ""
    image_a_path = ""
    image_b_path = ""
    image_c_path = ""
    analysis_model = DEFAULT_ANALYSIS_MODEL
    prompt_model = DEFAULT_PROMPT_MODEL
    image_model = DEFAULT_IMAGE_MODEL

    if request.method == "POST":
        action = request.form.get("action", "analyze")
        raw_content = request.form.get("raw_content", "").strip()
        analysis_model = request.form.get("analysis_model", DEFAULT_ANALYSIS_MODEL)
        prompt_model = request.form.get("prompt_model", DEFAULT_PROMPT_MODEL)
        image_model = request.form.get("image_model", DEFAULT_IMAGE_MODEL)
        analysis_text = request.form.get("analysis_text", "").strip()
        song_name = request.form.get("song_name", "").strip()
        artist = request.form.get("artist", "").strip()
        prompt_a = request.form.get("prompt_a", "").strip()
        prompt_b = request.form.get("prompt_b", "").strip()
        prompt_c = request.form.get("prompt_c", "").strip()
        image_a_path = request.form.get("image_a_path", "").strip()
        image_b_path = request.form.get("image_b_path", "").strip()
        image_c_path = request.form.get("image_c_path", "").strip()

        if not raw_content:
            error = "请输入歌曲信息（歌名/歌手/歌词）。"
        else:
            try:
                if action == "analyze":
                    full_response = analyze_lyrics(raw_content, model=analysis_model)
                    if full_response.startswith("Error during analysis:"):
                        raise RuntimeError(full_response)
                    analysis_text, song_name, artist = parse_analysis_response(full_response)
                elif action == "generate_prompts":
                    if not analysis_text:
                        raise RuntimeError("请先进行歌词赏析。")
                    if not song_name or not artist:
                        song_name = song_name or "Unknown_Song"
                        artist = artist or "Unknown_Artist"
                    visual_prompt = generate_visual_prompt(
                        song_name,
                        artist,
                        analysis_text,
                        model=prompt_model
                    )
                    prompts = [line for line in visual_prompt.splitlines() if line.strip()]
                    prompt_a = prompts[0] if len(prompts) > 0 else ""
                    prompt_b = prompts[1] if len(prompts) > 1 else ""
                    prompt_c = prompts[2] if len(prompts) > 2 else ""
                elif action in ("generate_images", "regenerate_a", "regenerate_b", "regenerate_c"):
                    if not (prompt_a or prompt_b or prompt_c):
                        raise RuntimeError("请先生成或填写提示词。")
                    os.makedirs(OUTPUT_DIR, exist_ok=True)
                    safe_name = song_name or "cover_image"

                    def save_image(prompt, suffix):
                        filename = f"{safe_name}_cover_{suffix}.png"
                        filepath = os.path.join(OUTPUT_DIR, filename)
                        generate_image(prompt, filepath, model=image_model)
                        return f"outputs/{filename}"

                    if action == "generate_images":
                        if prompt_a:
                            image_a_path = save_image(prompt_a, "A")
                        if prompt_b:
                            image_b_path = save_image(prompt_b, "B")
                        if prompt_c:
                            image_c_path = save_image(prompt_c, "C")
                    elif action == "regenerate_a" and prompt_a:
                        image_a_path = save_image(prompt_a, "A")
                    elif action == "regenerate_b" and prompt_b:
                        image_b_path = save_image(prompt_b, "B")
                    elif action == "regenerate_c" and prompt_c:
                        image_c_path = save_image(prompt_c, "C")
            except Exception as e:
                error = f"生成失败: {str(e)}"

        state_id = str(uuid.uuid4())
        STATE_STORE[state_id] = {
            "raw_content": raw_content,
            "analysis_text": analysis_text,
            "song_name": song_name,
            "artist": artist,
            "prompt_a": prompt_a,
            "prompt_b": prompt_b,
            "prompt_c": prompt_c,
            "image_a_path": image_a_path,
            "image_b_path": image_b_path,
            "image_c_path": image_c_path,
            "analysis_model": analysis_model,
            "prompt_model": prompt_model,
            "image_model": image_model,
            "error": error,
        }
        return redirect(url_for("index", state_id=state_id))

    state_id = request.args.get("state_id")
    if state_id and state_id in STATE_STORE:
        state = STATE_STORE[state_id]
        raw_content = state.get("raw_content", "")
        analysis_text = state.get("analysis_text", "")
        song_name = state.get("song_name", "")
        artist = state.get("artist", "")
        prompt_a = state.get("prompt_a", "")
        prompt_b = state.get("prompt_b", "")
        prompt_c = state.get("prompt_c", "")
        image_a_path = state.get("image_a_path", "")
        image_b_path = state.get("image_b_path", "")
        image_c_path = state.get("image_c_path", "")
        analysis_model = state.get("analysis_model", DEFAULT_ANALYSIS_MODEL)
        prompt_model = state.get("prompt_model", DEFAULT_PROMPT_MODEL)
        image_model = state.get("image_model", DEFAULT_IMAGE_MODEL)
        error = state.get("error")

    prompts = None
    images = []
    if prompt_a or prompt_b or prompt_c:
        prompts = [p for p in [prompt_a, prompt_b, prompt_c] if p]
    if image_a_path or image_b_path or image_c_path:
        images = [
            {"prompt": prompt_a, "image_path": image_a_path},
            {"prompt": prompt_b, "image_path": image_b_path},
            {"prompt": prompt_c, "image_path": image_c_path},
        ]

    return render_template(
        "index.html",
        raw_content=raw_content,
        result=result,
        error=error,
        prompts=prompts,
        images=images,
        disclaimer=DISCLAIMER,
        analysis_model=analysis_model,
        prompt_model=prompt_model,
        image_model=image_model,
        analysis_models=ANALYSIS_MODELS,
        prompt_models=PROMPT_MODELS,
        image_models=IMAGE_MODELS,
        analysis_text=analysis_text,
        song_name=song_name,
        artist=artist,
        prompt_a=prompt_a,
        prompt_b=prompt_b,
        prompt_c=prompt_c,
        image_a_path=image_a_path,
        image_b_path=image_b_path,
        image_c_path=image_c_path,
    )


if __name__ == "__main__":
    app.run(debug=True)
