# api_server.py (Instagram/Xのプロンプト切り替え対応)

from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
import io
import os
import base64

# --- APIキー設定 ---
api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyAhzaFRQSupPhM-sVaITAeP4aJ1o9JgRfw")
genai.configure(api_key=api_key)

# --- 使用するモデル ---
model = genai.GenerativeModel('gemini-2.5-flash')
app = Flask(__name__)

# --- プロンプトのテンプレートを定義 ---
INSTAGRAM_PROMPT_TEMPLATE = """
ここに複数の画像があります。これらの画像全体を一つのストーリーとして捉え、Instagram投稿文を作成してください。
{location_instruction}

# 作成の最重要ポイント
- **画像内の文字情報を活用**: 写真に写っている看板、メニュー、地名などを読み取り、投稿に具体性とリアリティを与えてください。
# その他のポイント
- **ストーリー性**: 一日の出来事や旅行の流れがわかるような、まとまりのあるストーリーにしてください。
- **感情表現**: 楽しさ、美味しさ、感動などが伝わるような、ポジティブな言葉を選んでください。
# 投稿文の形式
- 全体に関連する絵文字を3〜4個含めること。
- 全体に関連性が高く、人気のある日本語のハッシュタグを5個以上含めること。
"""

X_PROMPT_TEMPLATE = """
この1枚の画像を見て、X (旧Twitter) に投稿するための、短くてキャッチーな投稿文を作成してください。

# 作成のルール
- **簡潔さ**: 全体で140文字以内に収まるように、要点を簡潔にまとめてください。これが最も重要です。
- **インパクト**: ユーザーの目を引くような、面白いまたは魅力的な一言を冒頭に入れてください。
- **画像内の文字活用**: 写真に写っている面白い文字やキーワードがあれば、それも活用してください。
- **絵文字とハッシュタグ**: 関連する絵文字を1〜2個、話題になりそうなハッシュタグを2〜3個付けてください。
"""

@app.route('/generate-text', methods=['POST'])
def generate_text():
    data = request.get_json()
    if not data: return jsonify({'success': False, 'error': 'リクエストが不正です。'}), 400

    post_type = data.get('type')
    base64_images = data.get('images')

    if not post_type or not base64_images:
        return jsonify({'success': False, 'error': '投稿タイプまたは画像データが見つかりません。'}), 400

    # --- 機能タイプに応じてプロンプトを決定 ---
    if post_type == 'instagram':
        location = data.get('location', '')
        if location:
            location_instruction = f"今回は特に「{location}」での出来事として、その土地の魅力や雰囲気が伝わるように文章を構成してください。"
        else:
            location_instruction = "特定の地名は指定されていませんが、写真から感じ取れる場所の雰囲気を表現してください。"
        final_prompt = INSTAGRAM_PROMPT_TEMPLATE.format(location_instruction=location_instruction)
    
    elif post_type == 'twitter':
        final_prompt = X_PROMPT_TEMPLATE
    
    else:
        return jsonify({'success': False, 'error': '不明な投稿タイプです。'}), 400

    try:
        content_parts = [final_prompt]
        for b64_string in base64_images:
            img = Image.open(io.BytesIO(base64.b64decode(b64_string)))
            content_parts.append(img)
        
        response = model.generate_content(content_parts)
        if not response.parts:
            return jsonify({'success': False, 'error': '安全性設定により回答を生成できませんでした。'}), 400
        
        return jsonify({'success': True, 'text': response.text})

    except Exception as e:
        print(f"エラー発生: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)