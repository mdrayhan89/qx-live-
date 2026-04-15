<?php
header('Content-Type: application/json');
header("Access-Control-Allow-Origin: *"); // যাতে যেকোনো জায়গা থেকে API এক্সেস করা যায়

// ডাটাবেস কানেকশন (Render বা অন্য হোস্টিংয়ের DB Info দিন)
$conn = mysqli_connect("your_db_host", "your_db_user", "your_db_pass", "your_db_name");

if (!$conn) {
    die(json_encode(["success" => false, "message" => "Database Connection Failed"]));
}

// ডিফল্ট পেয়ার সেট করা
$pair = isset($_GET['pair']) ? mysqli_real_escape_string($conn, $_GET['pair']) : 'EURUSD_otc';

// ডাটাবেস থেকে লেটেস্ট ক্যান্ডেল আনা
$query = "SELECT * FROM candles WHERE pair = '$pair' LIMIT 1";
$result = mysqli_query($conn, $query);
$row = mysqli_fetch_assoc($result);

// আপনার দেওয়া স্পেসিফিক ফরম্যাট
$response = [
    "Owner_Developer" => "DARK-X-RAYHAN",
    "Telegram" => "@mdrayhan85",
    "Channel" => "https://t.me/mdrayhan85",
    "success" => true,
    "count" => $row ? 1 : 0,
    "data" => []
];

if ($row) {
    $response["data"][] = [
        "id" => $row['id'],
        "pair" => $row['pair'],
        "timeframe" => "M1",
        "candle_time" => $row['candle_time'],
        "open" => $row['open'],
        "high" => $row['high'],
        "low" => $row['low'],
        "close" => $row['close'],
        "volume" => "48", // এটি আপনি চাইলে পাইথন থেকে স্টোর করতে পারেন
        "color" => $row['color'],
        "created_at" => date("Y-m-d H:i:s")
    ];
}

echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
?>
