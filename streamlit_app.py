import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

# ==================================================
# 基本設定
# ==================================================

st.set_page_config(
    page_title="ねもちゃん市場",
    page_icon="🐱",
    layout="centered"
)

# ==================================================
# スマホ向けデザイン
# ==================================================

st.markdown("""
<style>

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 700px;
}

/* タイトル */
.nemo-title {
    font-size: 1.9rem;
    font-weight: 700;
    margin-bottom: 0.2rem;
}

.nemo-subtitle {
    font-size: 0.85rem;
    color: #777;
    margin-bottom: 1.5rem;
}

/* セクション見出し */
.section-title {
    font-size: 1.35rem;
    font-weight: 700;
    margin-top: 1.4rem;
    margin-bottom: 0.8rem;
}

.inn-title {
    font-size: 1.15rem;
    font-weight: 700;
    margin-bottom: 0.8rem;
}

/* 市場カード */
.market-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 1rem;
}

.market-card {
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: 10px 8px;
    text-align: center;
}

.market-name {
    font-size: 0.75rem;
    color: #666;
}

.market-price {
    font-size: 1rem;
    font-weight: 700;
    margin-top: 4px;
}

.market-up {
    font-size: 0.75rem;
    color: #18864b;
    margin-top: 4px;
}

.market-down {
    font-size: 0.75rem;
    color: #c63d3d;
    margin-top: 4px;
}

/* 星待館カード */
.game-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
}

.game-card {
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: 12px;
}

.game-label {
    font-size: 0.8rem;
    color: #666;
}

.game-value {
    font-size: 1.35rem;
    font-weight: 700;
    margin-top: 3px;
}

/* おたより */
.news-box {
    background: rgba(120,120,120,0.07);
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
    font-size: 0.9rem;
    line-height: 1.7;
}

.event-box {
    border: 1px solid #e0d7aa;
    border-radius: 12px;
    padding: 12px 14px;
    font-size: 0.9rem;
    line-height: 1.6;
    margin-top: 8px;
}

.small-note {
    font-size: 0.72rem;
    color: #888;
    margin-top: 10px;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# Supabase REST
# ==================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json"
}


def load_game():
    url = (
        f"{SUPABASE_URL}/rest/v1/game_state"
        "?id=eq.1&select=*"
    )

    response = requests.get(
        url,
        headers=SUPABASE_HEADERS,
        timeout=10
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise RuntimeError("game_state が見つかりません。")

    return rows[0]


def save_game(game):
    url = (
        f"{SUPABASE_URL}/rest/v1/game_state"
        "?id=eq.1"
    )

    data = {
        "level": game["level"],
        "total_sales": game["total_sales"],
        "nemo_energy": game["nemo_energy"],
        "guests": game["guests"],
        "last_update": game["last_update"]
    }

    response = requests.patch(
        url,
        headers={
            **SUPABASE_HEADERS,
            "Prefer": "return=minimal"
        },
        json=data,
        timeout=10
    )

    response.raise_for_status()


# ==================================================
# 仮想通貨市場
# ==================================================

@st.cache_data(ttl=300)
def get_market_data():

    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": "bitcoin,ethereum,solana",
        "vs_currencies": "jpy",
        "include_24hr_change": "true"
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


# ==================================================
# 星待館：1日1回成長
# ==================================================

def update_game_once_per_day(game, market):

    today = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).date().isoformat()

    # 今日はもう更新済み
    if game.get("last_update") == today:
        return game

    changes = [
        market["bitcoin"]["jpy_24h_change"],
        market["ethereum"]["jpy_24h_change"],
        market["solana"]["jpy_24h_change"]
    ]

    average_change = sum(changes) / len(changes)

    if average_change >= 5:
        guest_change = 5
        energy_change = 5

    elif average_change >= 2:
        guest_change = 3
        energy_change = 3

    elif average_change >= 0:
        guest_change = 1
        energy_change = 1

    elif average_change >= -3:
        guest_change = -1
        energy_change = -2

    else:
        guest_change = -3
        energy_change = -5

    new_guests = max(
        1,
        int(game["guests"]) + guest_change
    )

    # 宿泊客1人につき100G
    daily_sales = new_guests * 100

    new_total_sales = (
        int(game["total_sales"])
        + daily_sales
    )

    new_energy = min(
        100,
        max(
            0,
            int(game["nemo_energy"])
            + energy_change
        )
    )

    # 5000GごとにLvアップ
    new_level = (
        1
        + new_total_sales // 5000
    )

    updated = {
        "level": int(new_level),
        "total_sales": int(new_total_sales),
        "nemo_energy": int(new_energy),
        "guests": int(new_guests),
        "last_update": today
    }

    save_game(updated)

    return updated


# ==================================================
# データ取得
# ==================================================

try:

    market = get_market_data()
    game = load_game()

    game = update_game_once_per_day(
        game,
        market
    )

except Exception as e:

    st.error(
        "ねもちゃん市場の読み込みに失敗しました。"
    )

    st.code(str(e))

    st.stop()


# ==================================================
# タイトル
# ==================================================

st.markdown(
    '<div class="nemo-title">🐱 ねもちゃん市場</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="nemo-subtitle">'
    '現実の仮想通貨市場とつながる、ねもちゃんの世界'
    '</div>',
    unsafe_allow_html=True
)


# ==================================================
# 今日の市場
# ==================================================

st.markdown(
    '<div class="section-title">📈 今日の市場</div>',
    unsafe_allow_html=True
)

coins = [
    ("BTC", "bitcoin"),
    ("ETH", "ethereum"),
    ("SOL", "solana")
]

cards = ""

for symbol, coin_id in coins:

    price = market[coin_id]["jpy"]
    change = market[coin_id]["jpy_24h_change"]

    change_class = (
        "market-up"
        if change >= 0
        else "market-down"
    )

    arrow = "↑" if change >= 0 else "↓"

    cards += f"""
    <div class="market-card">
        <div class="market-name">{symbol}</div>
        <div class="market-price">
            ¥{price:,.0f}
        </div>
        <div class="{change_class}">
            {arrow} {change:+.2f}%
        </div>
    </div>
    """

st.markdown(
    f'<div class="market-grid">{cards}</div>',
    unsafe_allow_html=True
)


# ==================================================
# 今日の星待館
# ==================================================

st.markdown(
    '<div class="section-title">♨️ 今日の星待館</div>',
    unsafe_allow_html=True
)

st.markdown(
    f'<div class="inn-title">'
    f'⭐ 星待館 Lv.{game["level"]}'
    f'</div>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="game-grid">

        <div class="game-card">
            <div class="game-label">
                👥 宿泊客
            </div>
            <div class="game-value">
                {game["guests"]}人
            </div>
        </div>

        <div class="game-card">
            <div class="game-label">
                🐱 元気度
            </div>
            <div class="game-value">
                {game["nemo_energy"]} / 100
            </div>
        </div>

        <div class="game-card">
            <div class="game-label">
                💰 累計売上
            </div>
            <div class="game-value">
                {game["total_sales"]:,} G
            </div>
        </div>

        <div class="game-card">
            <div class="game-label">
                📅 最終更新
            </div>
            <div class="game-value"
                 style="font-size:1rem;">
                {game["last_update"]}
            </div>
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ==================================================
# 相場の雰囲気
# ==================================================

average_change = (
    market["bitcoin"]["jpy_24h_change"]
    + market["ethereum"]["jpy_24h_change"]
    + market["solana"]["jpy_24h_change"]
) / 3


# ==================================================
# 今日の星待館だより
# ==================================================

st.markdown(
    '<div class="section-title">📰 今日の星待館だより</div>',
    unsafe_allow_html=True
)

if average_change >= 5:

    market_news = (
        "🎉 市場はかなり好調。"
        "星待館にもお客さんが続々とやってきています。"
    )

    nemo_news = (
        "🐱 ねもちゃん絶好調。"
        "温泉街を元気いっぱい走り回っています。"
    )

elif average_change >= 2:

    market_news = (
        "🌸 市場は好調。"
        "星待館にお客さんが増えています。"
    )

    nemo_news = (
        "🐱 ねもちゃんご機嫌。"
        "今日は宿のお手伝いをしています。"
    )

elif average_change >= 0:

    market_news = (
        "🍵 市場は穏やか。"
        "星待館ものんびりした一日です。"
    )

    nemo_news = (
        "🐱 ねもちゃんは縁側でひと休み中。"
    )

elif average_change >= -3:

    market_news = (
        "🌧️ 市場は少し元気がありません。"
        "星待館も今日は静かです。"
    )

    nemo_news = (
        "🐱 ねもちゃんは温泉でのんびりしています。"
    )

else:

    market_news = (
        "⛈️ 市場は大荒れ。"
        "温泉街にも少し静かな空気が流れています。"
    )

    nemo_news = (
        "🐱 こんな日もあるよ、と"
        "ねもちゃんは温泉につかっています。"
    )


st.markdown(
    f"""
    <div class="news-box">
        {market_news}
    </div>

    <div class="news-box">
        {nemo_news}
    </div>

    <div class="news-box">
        🎁 売店に謎の新商品が入荷しました。
    </div>
    """,
    unsafe_allow_html=True
)


# ==================================================
# 特別イベント
# ==================================================

st.markdown(
    """
    <div class="event-box">
        🌌 <b>SPECIAL EVENT</b><br>
        今夜、星待館で花火大会が開催されます！
    </div>
    """,
    unsafe_allow_html=True
)


# ==================================================
# 更新時刻
# ==================================================

now = datetime.now(
    ZoneInfo("Asia/Tokyo")
)

st.markdown(
    f'<div class="small-note">'
    f'市場データ取得：{now.strftime("%Y/%m/%d %H:%M")}<br>'
    '星待館の状態は1日1回だけ変化します。'
    '</div>',
    unsafe_allow_html=True
)
