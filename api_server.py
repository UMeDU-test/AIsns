# api_server.py (フォームデータ受け取り対応版)

from flask import Flask, request, jsonify
import google.generativeai as genai
from PIL import Image
import io
import os

# --- APIキー設定 ---
# Renderの環境変数からAPIキーを読み込む
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("警告: 環境変数 'GOOGLE_API_KEY' が設定されていません。")

genai.configure(api_key=api_key)

# --- 使用するモデル ---
model = genai.GenerativeModel('gemini-1.5-flash-latest')
app = Flask(__name__)


# --- ★★★ 新しいエンドポイント `/generate-text-formdata` を定義 ★★★ ---
# これまでの `/generate-text` はもう使いません
@app.route('/generate-text-formdata', methods=['POST'])
def generate_text_formdata():
    try:
        # フォームデータからテキスト情報とファイル情報を取得
        # .get('key', 'default_value') はキーが存在しない場合にNoneではなくデフォルト値を返す
        post_type = request.form.get('type', '')
        location = request.form.get('location', '')
        
        # 'images[]' というキーで送られてくる全てのファイルを取得
        image_files = request.files.getlist('images[]')

        # 必須項目のチェック
        if not post_type or not image_files:
            return jsonify({'success': False, 'error': '投稿タイプまたは画像データが見つかりません。'}), 400

        # --- 機能タイプに応じてプロンプトを動的に決定 ---
        if post_type == 'instagram':
            if location:
                location_instruction = f"今回は特に「{location}」での出来事として、その土地の魅力や雰囲気が伝わるように文章を構成してください。"
            else:
                location_instruction = "特定の地名は指定されていませんが、写真から感じ取れる場所の雰囲気を表現してください。"
            
            # Instagram用のプロンプトを組み立て
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
            return jsonify({'success': False, 'error': '不明な投稿タイプです。'}), 400

        # --- AIへの送信データを作成 ---
        content_parts = [final_prompt]
        for image_file in image_files:
            # ファイルストリームを直接Pillowで開く
            img = Image.open(image_file.stream)
            content_parts.append(img)
        
        # Gemini APIにリクエストを送信
        response = model.generate_content(content_parts)

        # 安全性フィルターでブロックされた場合のチェック
        if not response.parts:
            return jsonify({'success': False, 'error': '安全性設定により回答を生成できませんでした。'}), 400
        
        # 成功レスポンスを返す
        return jsonify({'success': True, 'text': response.text})

    except Exception as e:
        # その他の予期せぬエラーを捕捉
        print(f"サーバー内部でエラーが発生しました: {e}")
        return jsonify({'success': False, 'error': 'サーバー内部でエラーが発生しました。'}), 500

if __name__ == '__main__':
    # この部分はローカルテスト用。Renderではgunicornが直接appを呼び出す
    app.run(host='0.0.0.0', port=5000, debug=True)
