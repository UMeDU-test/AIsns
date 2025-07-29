# api_server.py (Base64 JSON受け取り方式 - 完成版)

from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
import io
import os
import base64 # Base64ライブラリをインポート

# --- 1. APIキー設定 ---
# Renderの環境変数からAPIキーを読み込む
api_key = os.environ.get("AIzaSyAhzaFRQSupPhM-sVaITAeP4aJ1o9JgRfw")
if not api_key:
    print("警告: 環境変数 'GOOGLE_API_KEY' が設定されていません。")

# Google Generative AI を設定
genai.configure(api_key=api_key)

# --- 2. 使用するAIモデルを初期化 ---
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- 3. Flaskアプリケーションのインスタンスを作成 ---
app = Flask(__name__)


# --- 4. リクエストを受け取るためのエンドポイント(URLのパス)を定義 ---
# エンドポイント名は、PHP側の設定と合わせる
@app.route('/generate-text-base64', methods=['POST'])
def generate_text_base64():
    try:
        # --- 5. POSTされてきたJSONデータを取得 ---
        data = request.get_json()
        if not data or 'images' not in data or 'type' not in data:
            return jsonify({'success': False, 'error': 'リクエストデータが不正です。'}), 400

        # JSONデータから各値を取得
        post_type = data['type']
        location = data.get('location', '') # locationは任意なので.get()で安全に取得
        base64_images = data['images']
        
        # --- 6. 投稿タイプに応じてAIへの指示(プロンプト)を組み立てる ---
        if post_type == 'instagram':
            if location:
                location_instruction = f"今回は特に「{location}」での出来事として、その土地の魅力や雰囲気が伝わるように文章を構成してください。"
            else:
                location_instruction = "特定の地名は指定されていませんが、写真から感じ取れる場所の雰囲気を表現してください。"
            
            # Instagram用のプロンプト
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
            # X (Twitter)用のプロンプト
            final_prompt = """
            この1枚の画像を見て、X (旧Twitter) に投稿するための、短くてキャッチーな投稿文を作成してください。

            # 作成のルール
            - **簡潔さ**: 全体で140文字以内に収まるように、要点を簡潔にまとめてください。これが最も重要です。
            - **インパクト**: ユーザーの目を引くような、面白いまたは魅力的な一言を冒頭に入れてください。
            - **画像内の文字活用**: 写真に写っている面白い文字やキーワードがあれば、それも活用してください。
            - **絵文字とハッシュタグ**: 関連する絵文字を1〜2個、話題になりそうなハッシュタグを2〜3個付けてください。
            """
        else:
            # 想定外の投稿タイプが来た場合
            return jsonify({'success': False, 'error': '不明な投稿タイプです。'}), 400

        # --- 7. AIへの送信データを作成 ---
        # 最初にプロンプトを追加
        content_parts = [final_prompt]
        # 次に、Base64文字列をデコードして画像データに変換し、リストに追加
        for b64_string in base64_images:
            image_bytes = base64.b64decode(b64_string)
            img = Image.open(io.BytesIO(image_bytes))
            content_parts.append(img)
        
        # --- 8. Gemini APIにリクエストを送信 ---
        response = model.generate_content(content_parts)

        # 安全性フィルターでブロックされた場合のチェック
        if not response.parts:
            return jsonify({'success': False, 'error': '安全性設定により回答を生成できませんでした。'}), 400
        
        # --- 9. 成功レスポンスを返す ---
        return jsonify({'success': True, 'text': response.text})

    except Exception as e:
        # 予期せぬエラーが発生した場合の処理
        # (例: Base64デコード失敗、Pillowでの画像展開失敗など)
        print(f"サーバー内部でエラーが発生しました: {e}")
        return jsonify({'success': False, 'error': 'サーバー内部でエラーが発生しました。'}), 500

# --- 10. このスクリプトが直接実行された場合の処理 ---
# ローカルでのテスト実行時に使われる。Renderではgunicornが直接'app'を呼び出すため、この部分は使われない。
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
