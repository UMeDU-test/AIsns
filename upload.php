<?php
// upload.php (機能タイプ対応)

header('Content-Type: application/json');

$pythonApiUrl = 'http://localhost:5000/generate-text';
$response = ['success' => false, 'error' => '不明なエラーです。'];

// 機能タイプを受け取る (必須)
$type = isset($_POST['type']) ? $_POST['type'] : '';
if (empty($type)) {
    echo json_encode(['success' => false, 'error' => '投稿タイプが指定されていません。']);
    exit;
}

// Instagram用の場合のみ地名を受け取る
$location = ($type === 'instagram' && isset($_POST['location'])) ? $_POST['location'] : '';

if (isset($_FILES['images'])) {
    $files = $_FILES['images'];
    $base64Images = [];

    for ($i = 0; $i < count($files['name']); $i++) {
        $base64Images[] = base64_encode(file_get_contents($files['tmp_name'][$i]));
    }

    // Python APIに送信するデータに機能タイプを追加
    $postData = json_encode([
        'type' => $type,
        'location' => $location,
        'images' => $base64Images
    ]);

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $pythonApiUrl);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $postData);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json', 'Content-Length: ' . strlen($postData)]);
    
    $apiResponse = curl_exec($ch);
    $httpcode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpcode == 200 && $apiResponse) {
        echo $apiResponse;
        exit;
    } else {
        $response['error'] = 'APIサーバーとの通信に失敗しました。';
        $response['details'] = json_decode($apiResponse, true) ?? $apiResponse;
    }
} else {
    $response['error'] = 'アップロードされたファイルがありません。';
}

echo json_encode($response);