# api_server.py (フォームデータ受け取り対応版)

from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
import io
import os

# --- APIキー設定 ---
api_key = os.environ.get("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# --- 使用するモデル ---
model = genai.GenerativeModel('gemini-1.5-flash-latest')
app = Flask(__name__)

# --- プロンプトのテンプレート（変更なし） ---
INSTAGRAM_PROMPT_TEMPLATE = "..." # (内容は省略、元のままでOK)
X_PROMPT_TEMPLATE = "..." # (内容は省略、元のままでOK)

# --- ★★★ 新しいエンドポイントを追加 ★★★ ---
@app.route('/generate-text-formdata', methods=['POST'])
def generate_text_formdata():
    try:
        # フォームデータから値を取得
        post_type = request.form.get('type')
        location = request.form.get('location', '')
        # 複数の画像ファイルを取得
        image_files = request.files.getlist('images[]')

        if not post_type or not image_files:
            return jsonify({'success': False, 'error': '投稿タイプまたは画像データが見つかりません。'}), 400

        # --- プロンプトの決定ロジック (元のまま) ---
        if post_type == 'instagram':
            if location:
                location_instruction = f"今回は特に「{location}」での出来事として、その土地の魅力や雰囲気が伝わるように文章を構成してください。"
            else:
                location_instruction = "特定の地名は指定されていませんが、写真から感じ取れる場所の雰囲気を表現してください。"
            # f-stringを使ってテンプレートに埋め込む
            final_prompt = f"""
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
        elif post_type == 'twitter':
            final_prompt = """
            この1枚の画像を見て、X (旧Twitter) に投稿するための、短くてキャッチーな投稿文を作成してください。
            # 作成のルール
            - **簡潔さ**: 全体で140文字以内に収まるように、要点を簡潔にまとめてください。これが最も重要です。
            - **インパクト**: ユーザーの目を引くような、面白いまたは魅力的な一言を冒頭に入れてください。
            - **画像内の文字活用**: 写真に写っている面白い文字やキーワードがあれば、それも活用してください。
            - **絵文字とハッシュタグ**: 関連する絵文字を1〜2個、話題になりそうなハッシュタグを2〜3個付けてください。
            """
        else:
            return jsonify({'success': False, 'error': '不明な投稿タイプです。'}), 400

        # --- AIへの送信ロジック (元のまま) ---
        content_parts = [final_prompt]
        for image_file in image_files:
            img = Image.open(image_file.stream)
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
