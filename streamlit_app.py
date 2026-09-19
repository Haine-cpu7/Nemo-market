import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from supabase import create_client

st.set_page_config(
    page_title="ねもちゃん市場",
    page_icon="🐱",
    layout="centered"
)

# ----------------------------
# Supabase
# ----------------------------

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ----------------------------
# 仮想通貨価格
# ----------------------------

@st.cache_data(ttl=300)
def get_market_data():
    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": "bitcoin,ethereum,solana",
        "vs_currencies": "jpy",
        "include_24hr_change": "true"
    }

    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()

    return r.json()


# ----------------------------
# 星待館セーブデータ
# ----------------------------

def load_game():
    result = (
        supabase
        .table("game_state")
        .select("*")
        .eq("id", 1)
        .single()
        .execute()
    )

    return result.data


def save_game(data):
    (
        supabase
        .table("game_state")
        .update({
            "level": data["level"],
            "total_sales": data["total_sales"],
            "nemo_energy": data["nemo_energy"],
            "guests": data["guests"],
            "last_update": data["last_update"]
        })
        .eq("id", 1)
        .execute()
    )


# ----------------------------
# 今日1回だけ星待館を成長
# ----------------------------

def update_game_once_per_day(game, market):
    today = datetime.now(ZoneInfo("Asia/Tokyo")).date()

    if game["last_update"] == str(today):
        return game

    changes = [
        market["bitcoin"]["jpy_24h_change"],
        market["ethereum"]["jpy_24h_change"],
        market["solana"]["jpy_24h_change"]
    ]

    average_change = sum(changes) / len(changes)

    # 市場の雰囲気で宿泊客が変化
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

    new_guests = max(1, game["guests"] + guest_change)

    # 1人100G売上
    daily_sales = new_guests * 100

    new_total_sales = game["total_sales"] + daily_sales

    new_energy = min(
        100,
        max(0, game["nemo_energy"] + energy_change)
    )

    # 5000Gごとにレベルアップ
    new_level = 1 + (new_total_sales // 5000)

    updated = {
        "level": int(new_level),
        "total_sales": int(new_total_sales),
        "nemo_energy": int(new_energy),
        "guests": int(new_guests),
        "last_update": str(today)
    }

    save_game(updated)

    return updated


# ----------------------------
# 表示開始
# ----------------------------

st.title("🐱 ねもちゃん市場")

st.caption(
    "現実の仮想通貨市場とつながる、ねもちゃんの世界"
)

try:
    market = get_market_data()
    game = load_game()
    game = update_game_once_per_day(game, market)

except Exception as e:
    st.error("データの読み込みに失敗しました。")
    st.code(str(e))
    st.stop()


# ----------------------------
# 今日の市場
# ----------------------------

st.header("📈 今日の市場")

coins = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana"
}

for symbol, coin_id in coins.items():

    price = market[coin_id]["jpy"]
    change = market[coin_id]["jpy_24h_change"]

    st.metric(
        label=symbol,
        value=f"¥{price:,.0f}",
        delta=f"{change:+.2f}%"
    )


# ----------------------------
# 星待館
# ----------------------------

st.divider()

st.header("♨️ 今日の星待館")

st.subheader(
    f"⭐ 星待館 Lv.{game['level']}"
)

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "👥 宿泊客",
        f"{game['guests']}人"
    )

    st.metric(
        "💰 累計売上",
        f"{game['total_sales']:,} G"
    )

with col2:
    st.metric(
        "🐱 ねもちゃん元気度",
        f"{game['nemo_energy']} / 100"
    )

    st.metric(
        "📅 最終更新",
        game["last_update"]
    )


# ----------------------------
# 今日のねもちゃん
# ----------------------------

avg = (
    market["bitcoin"]["jpy_24h_change"]
    + market["ethereum"]["jpy_24h_change"]
    + market["solana"]["jpy_24h_change"]
) / 3

if avg >= 5:
    message = "🐱 今日は市場がお祭り騒ぎ。ねもちゃんも温泉街を走り回っています。"

elif avg >= 2:
    message = "🌸 市場は好調。星待館にもお客さんが増えています。"

elif avg >= 0:
    message = "🍵 穏やかな一日。ねもちゃんはのんびり宿番をしています。"

elif avg >= -3:
    message = "🌧️ 市場は少し元気がありません。ねもちゃんも今日は静かです。"

else:
    message = "⛈️ 市場は大荒れ。でも星待館の灯りは消えません。"

st.info(message)

st.caption(
    "市場データをもとに、星待館は1日1回だけ変化します。"
)
