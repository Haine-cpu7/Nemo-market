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
# スマホ向け文字サイズ
# ==================================================

st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
}

h1 {
    font-size: 1.8rem !important;
}

h2 {
    font-size: 1.35rem !important;
}

h3 {
    font-size: 1.1rem !important;
}

[data-testid="stMetricLabel"] p {
    font-size: 0.78rem !important;
}

[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.75rem !important;
}

[data-testid="stMetric"] {
    padding-top: 0.2rem;
    padding-bottom: 0.2rem;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# Supabase
# ==================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json"
}


def load_game():
    url = f"{SUPABASE_URL}/rest/v1/game_state?id=eq.1&select=*"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        raise RuntimeError("星待館のセーブデータが見つかりません。")

    return data[0]


def save_game(game):
    url = f"{SUPABASE_URL}/rest/v1/game_state?id=eq.1"

    payload = {
        "level": game["level"],
        "total_sales": game["total_sales"],
        "nemo_energy": game["nemo_energy"],
        "guests": game["guests"],
        "last_update": game["last_update"]
    }

    response = requests.patch(
        url,
        headers={
            **HEADERS,
            "Prefer": "return=minimal"
        },
        json=payload,
        timeout=10
    )

    response.raise_for_status()


# ==================================================
# 市場データ
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
# 星待館を1日1回成長
# ==================================================

def update_game_once_per_day(game, market):

    today = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).date().isoformat()

    # 今日すでに更新済みなら何もしない
    if game.get("last_update") == today:
        return game

    changes = [
        market["bitcoin"]["jpy_24h_change"],
        market["ethereum"]["jpy_24h_change"],
        market["solana"]["jpy_24h_change"]
    ]

    average_change = sum(changes) / 3

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

    guests = max(
        1,
        int(game["guests"]) + guest_change
    )

    total_sales = (
        int(game["total_sales"])
        + guests * 100
    )

    energy = min(
        100,
        max(
            0,
            int(game["nemo_energy"]) + energy_change
        )
    )

    level = 1 + total_sales // 5000

    updated = {
        "level": int(level),
        "total_sales": int(total_sales),
        "nemo_energy": int(energy),
        "guests": int(guests),
        "last_update": today
    }

    save_game(updated)

    return updated


# ==================================================
# 読み込み
# ==================================================

try:

    market = get_market_data()
    game = load_game()

    game = update_game_once_per_day(
        game,
        market
    )

except Exception as e:

    st.error("ねもちゃん市場の読み込みに失敗しました。")
    st.code(str(e))
    st.stop()


# ==================================================
# タイトル
# ==================================================

st.title("🐱 ねもちゃん市場")

st.caption(
    "現実の仮想通貨市場とつながる、ねもちゃんの世界"
)


# ==================================================
# 今日の市場
# ==================================================

st.header("📈 今日の市場")

btc, eth, sol = st.columns(3)

with btc:
    st.metric(
        "BTC",
        f"¥{market['bitcoin']['jpy']:,.0f}",
        f"{market['bitcoin']['jpy_24h_change']:+.2f}%"
    )

with eth:
    st.metric(
        "ETH",
        f"¥{market['ethereum']['jpy']:,.0f}",
        f"{market['ethereum']['jpy_24h_change']:+.2f}%"
    )

with sol:
    st.metric(
        "SOL",
        f"¥{market['solana']['jpy']:,.0f}",
        f"{market['solana']['jpy_24h_change']:+.2f}%"
    )


# ==================================================
# 星待館
# ==================================================

st.divider()

st.header("♨️ 今日の星待館")

st.subheader(
    f"⭐ 星待館 Lv.{game['level']}"
)

left, right = st.columns(2)

with left:
    st.metric(
        "👥 宿泊客",
        f"{game['guests']}人"
    )

    st.metric(
        "💰 累計売上",
        f"{game['total_sales']:,} G"
    )

with right:
    st.metric(
        "🐱 元気度",
        f"{game['nemo_energy']} / 100"
    )

    st.metric(
        "📅 最終更新",
        game["last_update"]
    )


# ==================================================
# 市場平均
# ==================================================

average_change = (
    market["bitcoin"]["jpy_24h_change"]
    + market["ethereum"]["jpy_24h_change"]
    + market["solana"]["jpy_24h_change"]
) / 3


# ==================================================
# 今日の星待館だより
# ==================================================

st.divider()

st.header("📰 今日の星待館だより")


if average_change >= 5:

    st.write(
        "🎉 市場はかなり好調。"
        "星待館にもお客さんが続々とやってきています。"
    )

    st.write(
        "🐱 ねもちゃん絶好調。"
        "温泉街を元気いっぱい走り回っています。"
    )


elif average_change >= 2:

    st.write(
        "🌸 市場は好調。"
        "星待館にお客さんが増えています。"
    )

    st.write(
        "🐱 ねもちゃんご機嫌。"
        "今日は宿のお手伝いをしています。"
    )


elif average_change >= 0:

    st.write(
        "🍵 市場は穏やか。"
        "星待館ものんびりした一日です。"
    )

    st.write(
        "🐱 ねもちゃんは縁側でひと休み中。"
    )


elif average_change >= -3:

    st.write(
        "🌧️ 市場は少し元気がありません。"
        "星待館も今日は静かです。"
    )

    st.write(
        "🐱 ねもちゃんは温泉でのんびりしています。"
    )


else:

    st.write(
        "⛈️ 市場は大荒れ。"
        "温泉街にも静かな空気が流れています。"
    )

    st.write(
        "🐱 「こんな日もあるよ」と、"
        "ねもちゃんは温泉につかっています。"
    )


st.write(
    "🎁 売店に謎の新商品が入荷しました。"
)


# ==================================================
# イベント
# ==================================================

st.info(
    "🌌 SPECIAL EVENT："
    "今夜、星待館で花火大会が開催されます！"
)


# ==================================================
# 更新時刻
# ==================================================

now = datetime.now(
    ZoneInfo("Asia/Tokyo")
)

st.caption(
    f"市場データ取得：{now.strftime('%Y/%m/%d %H:%M')}"
)

st.caption(
    "星待館の状態は1日1回だけ変化します。"
)
