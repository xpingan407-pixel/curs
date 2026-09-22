<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, X-Game-Token');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

const DATA_DIR = __DIR__ . '/data';
const INITIAL_BALANCE = 10000;
const MIN_BET = 10;
const MAX_BET = 5000;

$action = $_GET['action'] ?? '';

try {
    match ($action) {
        'init' => jsonResponse(handleInit()),
        'status' => jsonResponse(handleStatus()),
        'play' => jsonResponse(handlePlay()),
        default => throw new InvalidArgumentException('未知 action'),
    };
} catch (InvalidArgumentException $e) {
    jsonResponse(['ok' => false, 'message' => $e->getMessage()], 400);
} catch (Throwable $e) {
    jsonResponse(['ok' => false, 'message' => '服务器错误'], 500);
}

function jsonResponse(array $data, int $code = 200): void
{
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function ensureDataDir(): void
{
    if (!is_dir(DATA_DIR) && !mkdir(DATA_DIR, 0755, true)) {
        throw new RuntimeException('无法创建数据目录');
    }
}

function readPlayer(string $token): ?array
{
    $path = playerPath($token);
    if (!is_file($path)) {
        return null;
    }
    $raw = file_get_contents($path);
    if ($raw === false) {
        return null;
    }
    $data = json_decode($raw, true);
    return is_array($data) ? $data : null;
}

function writePlayer(string $token, array $player): void
{
    ensureDataDir();
    $path = playerPath($token);
    file_put_contents($path, json_encode($player, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
}

function playerPath(string $token): string
{
    if (!preg_match('/^[a-f0-9]{32}$/', $token)) {
        throw new InvalidArgumentException('无效 token');
    }
    return DATA_DIR . '/' . $token . '.json';
}

function requireToken(): string
{
    $token = $_SERVER['HTTP_X_GAME_TOKEN'] ?? '';
    if ($token === '') {
        throw new InvalidArgumentException('缺少 X-Game-Token');
    }
    return $token;
}

function handleInit(): array
{
    ensureDataDir();
    $token = bin2hex(random_bytes(16));
    $player = [
        'balance' => INITIAL_BALANCE,
        'last' => null,
        'history' => [],
    ];
    writePlayer($token, $player);

    return [
        'ok' => true,
        'token' => $token,
        'balance' => $player['balance'],
        'rules' => gameRules(),
    ];
}

function handleStatus(): array
{
    $token = requireToken();
    $player = readPlayer($token);
    if ($player === null) {
        throw new InvalidArgumentException('会话无效，请重新进入游戏');
    }

    return [
        'ok' => true,
        'balance' => (int) $player['balance'],
        'last' => $player['last'],
        'history' => array_slice($player['history'] ?? [], 0, 10),
        'rules' => gameRules(),
    ];
}

function handlePlay(): array
{
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        throw new InvalidArgumentException('请使用 POST');
    }

    $token = requireToken();
    $player = readPlayer($token);
    if ($player === null) {
        throw new InvalidArgumentException('会话无效，请重新进入游戏');
    }

    $body = json_decode(file_get_contents('php://input') ?: '{}', true);
    if (!is_array($body)) {
        throw new InvalidArgumentException('请求体无效');
    }

    $betType = (string) ($body['betType'] ?? '');
    $amount = (int) ($body['amount'] ?? 0);

    if (!in_array($betType, ['big', 'small', 'odd', 'even'], true)) {
        throw new InvalidArgumentException('请选择：大、小、单或双');
    }
    if ($amount < MIN_BET || $amount > MAX_BET) {
        throw new InvalidArgumentException('下注金额须在 ' . MIN_BET . '～' . MAX_BET . ' 之间');
    }
    if ($amount > (int) $player['balance']) {
        throw new InvalidArgumentException('余额不足');
    }

    $dice = [random_int(1, 6), random_int(1, 6), random_int(1, 6)];
    $sum = array_sum($dice);
    $triple = $dice[0] === $dice[1] && $dice[1] === $dice[2];
    $win = resolveBet($betType, $sum, $triple);

    $balance = (int) $player['balance'];
    if ($win) {
        $balance += $amount;
    } else {
        $balance -= $amount;
    }

    $record = [
        'dice' => $dice,
        'sum' => $sum,
        'triple' => $triple,
        'betType' => $betType,
        'betLabel' => betLabel($betType),
        'amount' => $amount,
        'win' => $win,
        'balance' => $balance,
        'time' => date('Y-m-d H:i:s'),
    ];

    $history = $player['history'] ?? [];
    array_unshift($history, $record);
    $history = array_slice($history, 0, 20);

    $player['balance'] = $balance;
    $player['last'] = $record;
    $player['history'] = $history;
    writePlayer($token, $player);

    return [
        'ok' => true,
        'result' => $record,
        'balance' => $balance,
        'message' => buildResultMessage($record),
    ];
}

function resolveBet(string $betType, int $sum, bool $triple): bool
{
    if ($triple) {
        return false;
    }
    if ($sum === 3 || $sum === 18) {
        if ($betType === 'big' || $betType === 'small') {
            return false;
        }
    }

    return match ($betType) {
        'big' => $sum >= 11 && $sum <= 17,
        'small' => $sum >= 4 && $sum <= 10,
        'odd' => $sum % 2 === 1,
        'even' => $sum % 2 === 0,
        default => false,
    };
}

function betLabel(string $betType): string
{
    return match ($betType) {
        'big' => '大',
        'small' => '小',
        'odd' => '单',
        'even' => '双',
        default => $betType,
    };
}

function buildResultMessage(array $record): string
{
    $diceStr = implode(',', $record['dice']);
    if ($record['triple']) {
        $extra = '豹子，本局通杀';
    } elseif ($record['sum'] === 3 || $record['sum'] === 18) {
        $extra = '围骰点数，猜大小无效';
    } else {
        $extra = '';
    }

    $outcome = $record['win'] ? '赢 +' . $record['amount'] : '输 -' . $record['amount'];
    return "骰子 [{$diceStr}] 总和 {$record['sum']}，押{$record['betLabel']} {$outcome}" . ($extra ? "（{$extra}）" : '');
}

function gameRules(): array
{
    return [
        'diceCount' => 3,
        'big' => '三骰总和 11～17 为大（豹子或 3/18 点押大小判负）',
        'small' => '三骰总和 4～10 为小（豹子或 3/18 点押大小判负）',
        'odd' => '总和为单数（豹子判负）',
        'even' => '总和为双数（豹子判负）',
        'payout' => '1:1（赢返还本金并赢得等额筹码）',
        'minBet' => MIN_BET,
        'maxBet' => MAX_BET,
    ];
}
