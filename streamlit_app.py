import streamlit as st
import requests
import random
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
# スマホ向け表示
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


# ==================================================
# 星待館データ
# ==================================================

def load_game():

    url = (
        f"{SUPABASE_URL}/rest/v1/game_state"
        "?id=eq.1&select=*"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise RuntimeError(
            "星待館のセーブデータが見つかりません。"
        )

    return rows[0]


def save_game(game):

    url = (
        f"{SUPABASE_URL}/rest/v1/game_state"
        "?id=eq.1"
    )

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

    url = (
        "https://api.coingecko.com/api/v3/"
        "simple/price"
    )

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
            int(game["nemo_energy"])
            + energy_change
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
# 釣り場データ
# ==================================================

FISH_LIST = [
    {
        "name": "フナ",
        "rarity": "★",
        "weight": 30,
        "min_size": 12.0,
        "max_size": 30.0,
        "note": "ねもちゃんでも釣りやすい、おなじみの魚。"
    },
    {
        "name": "コイ",
        "rarity": "★",
        "weight": 25,
        "min_size": 25.0,
        "max_size": 65.0,
        "note": "星待川をゆっくり泳ぐ大きなコイ。"
    },
    {
        "name": "アユ",
        "rarity": "★★",
        "weight": 18,
        "min_size": 15.0,
        "max_size": 28.0,
        "note": "きれいな水に住む、すらっとした魚。"
    },
    {
        "name": "ニジマス",
        "rarity": "★★",
        "weight": 14,
        "min_size": 20.0,
        "max_size": 45.0,
        "note": "虹色に光る、星待川の人気者。"
    },
    {
        "name": "ナマズ",
        "rarity": "★★★",
        "weight": 8,
        "min_size": 35.0,
        "max_size": 80.0,
        "note": "川底から突然あらわれる大物。"
    },
    {
        "name": "金色のコイ",
        "rarity": "★★★★",
        "weight": 4,
        "min_size": 30.0,
        "max_size": 70.0,
        "note": "夕日に照らされると金色に輝く珍しいコイ。"
    },
    {
        "name": "星待ヌシ",
        "rarity": "★★★★★",
        "weight": 1,
        "min_size": 80.0,
        "max_size": 130.0,
        "note": "星待川に昔から住むと言われる伝説の魚。"
    }
]


def get_today_catch():

    today = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).date().isoformat()

    url = (
        f"{SUPABASE_URL}/rest/v1/fishing_log"
        f"?fishing_date=eq.{today}&select=*"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    rows = response.json()

    if rows:
        return rows[0]

    return None


def get_recent_catches():

    url = (
        f"{SUPABASE_URL}/rest/v1/fishing_log"
        "?select=*"
        "&order=fishing_date.desc"
        "&limit=10"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10
    )

    response.raise_for_status()

    return response.json()


def catch_fish():

    today = datetime.now(
        ZoneInfo("Asia/Tokyo")
    ).date().isoformat()

    fish = random.choices(
        FISH_LIST,
        weights=[
            item["weight"]
            for item in FISH_LIST
        ],
        k=1
    )[0]

    size = round(
        random.uniform(
            fish["min_size"],
            fish["max_size"]
        ),
        1
    )

    payload = {
        "fishing_date": today,
        "fish_name": fish["name"],
        "rarity": fish["rarity"],
        "size_cm": size,
        "note": fish["note"]
    }

    url = (
        f"{SUPABASE_URL}/rest/v1/fishing_log"
    )

    response = requests.post(
        url,
        headers={
            **HEADERS,
            "Prefer": "return=representation"
        },
        json=payload,
        timeout=10
    )

    # 誰かがほぼ同時に釣った場合、
    # 先に保存された今日の魚を表示する
    if response.status_code == 409:
        return get_today_catch()

    response.raise_for_status()

    rows = response.json()

    if rows:
        return rows[0]

    return get_today_catch()


# ==================================================
# 共通データ読み込み
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

st.title("🐱 ねもちゃん市場")

st.caption(
    "現実の仮想通貨市場とつながる、"
    "ねもちゃんの小さな世界"
)


# ==================================================
# ページ切り替え
# ==================================================

market_tab, fishing_tab = st.tabs(
    [
        "📈 市場・星待館",
        "🎣 釣り場"
    ]
)


# ==================================================
# 市場・星待館
# ==================================================

with market_tab:

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


    average_change = (
        market["bitcoin"]["jpy_24h_change"]
        + market["ethereum"]["jpy_24h_change"]
        + market["solana"]["jpy_24h_change"]
    ) / 3


    st.divider()

    st.header("📰 今日の星待館だより")


    if average_change >= 5:

        st.write(
            "🎉 市場はかなり好調。"
            "星待館にもお客さんが"
            "続々とやってきています。"
        )

        st.write(
            "🐱 ねもちゃん絶好調。"
            "温泉街を元気いっぱい"
            "走り回っています。"
        )


    elif average_change >= 2:

        st.write(
            "🌸 市場は好調。"
            "星待館にお客さんが"
            "増えています。"
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
            "🐱 ねもちゃんは"
            "縁側でひと休み中。"
        )


    elif average_change >= -3:

        st.write(
            "🌧️ 市場は少し元気がありません。"
            "星待館も今日は静かです。"
        )

        st.write(
            "🐱 ねもちゃんは"
            "温泉でのんびりしています。"
        )


    else:

        st.write(
            "⛈️ 市場は大荒れ。"
            "温泉街にも静かな空気が"
            "流れています。"
        )

        st.write(
            "🐱 「こんな日もあるよ」と、"
            "ねもちゃんは温泉につかっています。"
        )


    st.write(
        "🎁 売店に謎の新商品が入荷しました。"
    )


    st.info(
        "🌌 SPECIAL EVENT："
        "今夜、星待館で花火大会が開催されます！"
    )


# ==================================================
# 釣り場
# ==================================================

with fishing_tab:

    st.header("🎣 ねもちゃん釣り場")

    st.write(
        "星待館のそばを流れる「星待川」。"
    )

    st.write(
        "1日1回だけ、"
        "ねもちゃんが釣りに出かけます。"
    )

    try:

        today_catch = get_today_catch()

    except Exception as e:

        st.error(
            "釣り場の読み込みに失敗しました。"
        )

        st.code(str(e))

        st.stop()


    # ----------------------------------------------
    # まだ今日釣っていない
    # ----------------------------------------------

    if today_catch is None:

        st.info(
            "🐾 今日はまだ釣りをしていません。"
        )

        if st.button(
            "🎣 今日の釣りをする",
            use_container_width=True
        ):

            try:

                today_catch = catch_fish()

                st.success(
                    "ねもちゃんが何か釣った！"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "釣りに失敗しました。"
                )

                st.code(str(e))


    # ----------------------------------------------
    # 今日の釣果
    # ----------------------------------------------

    else:

        st.success(
            "🐱 今日はもう釣りました！"
        )

        st.subheader("🐟 今日の釣果")

        st.metric(
            "魚",
            today_catch["fish_name"]
        )

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "レア度",
                today_catch["rarity"]
            )

        with col2:

            st.metric(
                "サイズ",
                f'{today_catch["size_cm"]} cm'
            )

        st.write(
            f'💬 {today_catch["note"]}'
        )

        st.caption(
            "また明日、釣りに来よう。"
        )


    # ----------------------------------------------
    # 最近の釣果
    # ----------------------------------------------

    st.divider()

    st.subheader("📖 最近の釣果")

    try:

        recent = get_recent_catches()

    except Exception:

        recent = []


    if recent:

        for catch in recent[:5]:

            st.write(
                f'**{catch["fishing_date"]}**　'
                f'{catch["fish_name"]}　'
                f'{catch["size_cm"]}cm　'
                f'{catch["rarity"]}'
            )

    else:

        st.caption(
            "まだ釣果がありません。"
        )


    # ----------------------------------------------
    # 魚図鑑
    # ----------------------------------------------

    st.divider()

    st.subheader("📚 魚図鑑")

    caught_names = {
        catch["fish_name"]
        for catch in recent
    }

    total_species = len(FISH_LIST)

    discovered = sum(
        1
        for fish in FISH_LIST
        if fish["name"] in caught_names
    )

    st.write(
        f"**{discovered} / {total_species} 種類発見**"
    )


    for fish in FISH_LIST:

        if fish["name"] in caught_names:

            st.write(
                f'🐟 **{fish["name"]}** '
                f'{fish["rarity"]}'
            )

        else:

            st.write(
                "❓ **？？？**"
            )


    st.caption(
        "いろんな魚を釣って、"
        "図鑑を埋めよう。"
    )


# ==================================================
# 共通フッター
# ==================================================

st.divider()

now = datetime.now(
    ZoneInfo("Asia/Tokyo")
)

st.caption(
    f"市場データ取得："
    f"{now.strftime('%Y/%m/%d %H:%M')}"
)

st.caption(
    "星待館は1日1回、"
    "現実の市場に合わせて変化します。"
)

st.caption(
    "釣り場の釣果も1日1回記録されます。"
)
