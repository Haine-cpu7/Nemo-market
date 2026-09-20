import re
import random
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import streamlit as st


# ==================================================
# 基本設定
# ==================================================

st.set_page_config(
    page_title="Nemo Garden",
    page_icon="🐱",
    layout="centered",
)


# ==================================================
# スマホ向け表示
# ==================================================

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)


# ==================================================
# 共通設定
# ==================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Content-Type": "application/json",
}

TOKYO = ZoneInfo("Asia/Tokyo")


def today_str():
    return datetime.now(TOKYO).date().isoformat()


# ==================================================
# 市場データ
# ==================================================

@st.cache_data(ttl=300)
def get_market_data():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin,ethereum,solana",
        "vs_currencies": "jpy",
        "include_24hr_change": "true",
    }

    response = requests.get(
        url,
        params=params,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


# ==================================================
# 星待館
# ==================================================

def load_game():
    url = (
        f"{SUPABASE_URL}/rest/v1/game_state"
        "?id=eq.1&select=*"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
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
        "last_update": game["last_update"],
        "shop_coins": game.get("shop_coins", 0),
    }

    response = requests.patch(
        url,
        headers={
            **HEADERS,
            "Prefer": "return=minimal",
        },
        json=payload,
        timeout=10,
    )
    response.raise_for_status()


def update_game_once_per_day(game, market):
    today = today_str()

    if game.get("last_update") == today:
        return game

    changes = [
        market["bitcoin"]["jpy_24h_change"],
        market["ethereum"]["jpy_24h_change"],
        market["solana"]["jpy_24h_change"],
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
        int(game["guests"]) + guest_change,
    )

    daily_sales = guests * 100
    total_sales = int(game["total_sales"]) + daily_sales

    shop_coins = (
        int(game.get("shop_coins", 0))
        + daily_sales
    )

    energy = min(
        100,
        max(
            0,
            int(game["nemo_energy"]) + energy_change,
        ),
    )

    level = 1 + total_sales // 5000

    updated = {
        "level": int(level),
        "total_sales": int(total_sales),
        "shop_coins": int(shop_coins),
        "nemo_energy": int(energy),
        "guests": int(guests),
        "last_update": today,
    }

    save_game(updated)
    return updated


# ==================================================
# 釣り場
# ==================================================

FISH_LIST = [
    {
        "name": "フナ",
        "rarity": "★",
        "weight": 30,
        "min_size": 12.0,
        "max_size": 30.0,
        "note": "ねもちゃんでも釣りやすい、おなじみの魚。",
    },
    {
        "name": "コイ",
        "rarity": "★",
        "weight": 25,
        "min_size": 25.0,
        "max_size": 65.0,
        "note": "星待川をゆっくり泳ぐ大きなコイ。",
    },
    {
        "name": "アユ",
        "rarity": "★★",
        "weight": 18,
        "min_size": 15.0,
        "max_size": 28.0,
        "note": "きれいな水に住む、すらっとした魚。",
    },
    {
        "name": "ニジマス",
        "rarity": "★★",
        "weight": 14,
        "min_size": 20.0,
        "max_size": 45.0,
        "note": "虹色に光る、星待川の人気者。",
    },
    {
        "name": "ナマズ",
        "rarity": "★★★",
        "weight": 8,
        "min_size": 35.0,
        "max_size": 80.0,
        "note": "川底から突然あらわれる大物。",
    },
    {
        "name": "金色のコイ",
        "rarity": "★★★★",
        "weight": 4,
        "min_size": 30.0,
        "max_size": 70.0,
        "note": "夕日に照らされると金色に輝く珍しいコイ。",
    },
    {
        "name": "星待ヌシ",
        "rarity": "★★★★★",
        "weight": 1,
        "min_size": 80.0,
        "max_size": 130.0,
        "note": "星待川に昔から住むと言われる伝説の魚。",
    },
]


def get_today_catch():
    today = today_str()

    url = (
        f"{SUPABASE_URL}/rest/v1/fishing_log"
        f"?fishing_date=eq.{today}&select=*"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()

    rows = response.json()
    return rows[0] if rows else None


def get_recent_catches(limit=30):
    url = (
        f"{SUPABASE_URL}/rest/v1/fishing_log"
        "?select=*"
        "&order=fishing_date.desc"
        f"&limit={limit}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def catch_fish():
    today = today_str()

    fish = random.choices(
        FISH_LIST,
        weights=[item["weight"] for item in FISH_LIST],
        k=1,
    )[0]

    size = round(
        random.uniform(
            fish["min_size"],
            fish["max_size"],
        ),
        1,
    )

    payload = {
        "fishing_date": today,
        "fish_name": fish["name"],
        "rarity": fish["rarity"],
        "size_cm": size,
        "note": fish["note"],
    }

    url = f"{SUPABASE_URL}/rest/v1/fishing_log"

    response = requests.post(
        url,
        headers={
            **HEADERS,
            "Prefer": "return=representation",
        },
        json=payload,
        timeout=10,
    )

    if response.status_code == 409:
        return get_today_catch()

    response.raise_for_status()

    rows = response.json()
    return rows[0] if rows else get_today_catch()


# ==================================================
# 庭園
# ==================================================

PLANT_LIST = [
    {
        "name": "たんぽぽ",
        "rarity": "★",
        "weight": 32,
        "emoji": "🌼",
    },
    {
        "name": "クローバー",
        "rarity": "★",
        "weight": 28,
        "emoji": "🍀",
    },
    {
        "name": "チューリップ",
        "rarity": "★★",
        "weight": 20,
        "emoji": "🌷",
    },
    {
        "name": "桜草",
        "rarity": "★★★",
        "weight": 12,
        "emoji": "🌸",
    },
    {
        "name": "青い星花",
        "rarity": "★★★★",
        "weight": 6,
        "emoji": "💠",
    },
    {
        "name": "星待花",
        "rarity": "★★★★★",
        "weight": 2,
        "emoji": "✨",
    },
]


def load_garden():
    url = (
        f"{SUPABASE_URL}/rest/v1/garden_state"
        "?id=eq.1&select=*"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()

    rows = response.json()

    if not rows:
        raise RuntimeError(
            "庭園のセーブデータが見つかりません。"
        )

    return rows[0]


def save_garden(garden):
    url = (
        f"{SUPABASE_URL}/rest/v1/garden_state"
        "?id=eq.1"
    )

    payload = {
        "plant_name": garden["plant_name"],
        "rarity": garden["rarity"],
        "growth_stage": garden["growth_stage"],
        "started_date": garden["started_date"],
        "last_tended_date": garden["last_tended_date"],
        "blooms": garden["blooms"],
    }

    response = requests.patch(
        url,
        headers={
            **HEADERS,
            "Prefer": "return=minimal",
        },
        json=payload,
        timeout=10,
    )
    response.raise_for_status()


def add_bloom_log(plant_name, rarity):
    payload = {
        "bloom_date": today_str(),
        "plant_name": plant_name,
        "rarity": rarity,
    }

    url = f"{SUPABASE_URL}/rest/v1/garden_log"

    response = requests.post(
        url,
        headers={
            **HEADERS,
            "Prefer": "return=minimal",
        },
        json=payload,
        timeout=10,
    )
    response.raise_for_status()


def get_garden_log(limit=100):
    url = (
        f"{SUPABASE_URL}/rest/v1/garden_log"
        "?select=*"
        "&order=bloom_date.desc"
        f"&limit={limit}"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def choose_plant():
    return random.choices(
        PLANT_LIST,
        weights=[item["weight"] for item in PLANT_LIST],
        k=1,
    )[0]


def tend_garden(garden):
    today = today_str()

    if garden.get("last_tended_date") == today:
        return garden, "already"

    if (
        not garden.get("plant_name")
        or int(garden.get("growth_stage", 0)) >= 3
    ):
        plant = choose_plant()

        updated = {
            "plant_name": plant["name"],
            "rarity": plant["rarity"],
            "growth_stage": 1,
            "started_date": today,
            "last_tended_date": today,
            "blooms": int(garden.get("blooms", 0)),
        }

        save_garden(updated)
        return updated, "planted"

    stage = int(garden.get("growth_stage", 0))

    if stage == 1:
        updated = {
            **garden,
            "growth_stage": 2,
            "last_tended_date": today,
        }

        save_garden(updated)
        return updated, "grown"

    if stage == 2:
        updated = {
            **garden,
            "growth_stage": 3,
            "last_tended_date": today,
            "blooms": int(garden.get("blooms", 0)) + 1,
        }

        save_garden(updated)
        add_bloom_log(
            updated["plant_name"],
            updated["rarity"],
        )
        return updated, "bloomed"

    return garden, "already"


def get_plant_meta(name):
    for plant in PLANT_LIST:
        if plant["name"] == name:
            return plant

    return {
        "name": name or "？？？",
        "rarity": "",
        "emoji": "🌱",
    }


def garden_stage_text(garden):
    stage = int(garden.get("growth_stage", 0))
    plant = get_plant_meta(garden.get("plant_name"))

    if stage == 0 or not garden.get("plant_name"):
        return "🪴 まだ何も植わっていません。"

    if stage == 1:
        return (
            f"🌱 {plant['name']}の芽が出ました。"
            "まだ小さいけれど、元気に育っています。"
        )

    if stage == 2:
        return (
            f"🌿 {plant['name']}の葉が増えてきました。"
            "もう少しで花が咲きそうです。"
        )

    return (
        f"{plant['emoji']} "
        f"{plant['name']}が咲きました！ "
        f"{garden.get('rarity', '')}"
    )


# ==================================================
# 売店
# ==================================================

SHOP_ITEMS = [
    {
        "key": "onsen_manju",
        "emoji": "🍡",
        "name": "温泉まんじゅう",
        "price": 300,
        "description": "星待館名物。ねもちゃんのおやつ。",
    },
    {
        "key": "good_rod",
        "emoji": "🎣",
        "name": "いい釣り竿",
        "price": 500,
        "description": "ちょっと立派な釣り竿。",
    },
    {
        "key": "watering_can",
        "emoji": "🪣",
        "name": "お庭のじょうろ",
        "price": 400,
        "description": "庭園のお世話にぴったり。",
    },
    {
        "key": "lucky_charm",
        "emoji": "🍀",
        "name": "幸運のお守り",
        "price": 1200,
        "description": "なんとなく良いことがありそう。",
    },
    {
        "key": "star_lantern",
        "emoji": "🏮",
        "name": "星待ランタン",
        "price": 3000,
        "description": "星待館を優しく照らす特別なランタン。",
    },
]


def get_inventory():
    url = (
        f"{SUPABASE_URL}/rest/v1/shop_inventory"
        "?select=*"
        "&order=purchased_at.asc"
    )

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def get_available_coins(game, inventory):
    earned = int(game.get("shop_coins", 0))

    spent = sum(
        int(item.get("price", 0))
        for item in inventory
    )

    return max(0, earned - spent)


def buy_item(item, game, inventory):
    owned_keys = {
        row["item_key"]
        for row in inventory
    }

    if item["key"] in owned_keys:
        return "owned"

    available = get_available_coins(
        game,
        inventory,
    )

    if available < item["price"]:
        return "not_enough"

    payload = {
        "item_key": item["key"],
        "item_name": item["name"],
        "price": item["price"],
    }

    url = f"{SUPABASE_URL}/rest/v1/shop_inventory"

    response = requests.post(
        url,
        headers={
            **HEADERS,
            "Prefer": "return=representation",
        },
        json=payload,
        timeout=10,
    )

    if response.status_code == 409:
        return "owned"

    response.raise_for_status()
    return "purchased"


# ==================================================
# 秘密の庭 / NFTホルダー判定
# ==================================================

COLLECTION_SLUG = "nemocollection2023"

OPENSEA_AUTH_URL = (
    "https://api.opensea.io/api/v2/auth/keys"
)

OPENSEA_ACCOUNT_NFTS_URL = (
    "https://api.opensea.io/api/v2/chain/"
    "{chain}/account/{address}/nfts"
)

ADDRESS_RE = re.compile(
    r"^0x[a-fA-F0-9]{40}$"
)


@st.cache_resource(ttl=6 * 24 * 60 * 60)
def get_opensea_api_key():
    try:
        configured_key = st.secrets["OPENSEA_API_KEY"]
    except Exception:
        configured_key = ""

    if configured_key:
        return configured_key

    response = requests.post(
        OPENSEA_AUTH_URL,
        timeout=15,
    )
    response.raise_for_status()

    payload = response.json()
    api_key = payload.get("api_key")

    if not api_key:
        raise RuntimeError(
            "OpenSea API keyを取得できませんでした。"
        )

    return api_key


@st.cache_data(ttl=60, show_spinner=False)
def get_nemo_nfts(address):
    api_key = get_opensea_api_key()

    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }

    chain_candidates = (
        "polygon",
        "matic",
    )

    last_error = None

    for chain in chain_candidates:
        url = OPENSEA_ACCOUNT_NFTS_URL.format(
            chain=chain,
            address=address,
        )

        try:
            response = requests.get(
                url,
                headers=headers,
                params={
                    "collection": COLLECTION_SLUG,
                    "include_auto_hidden": "true",
                    "limit": 20,
                },
                timeout=20,
            )
        except requests.RequestException as exc:
            last_error = exc
            continue

        if response.status_code == 200:
            payload = response.json()
            return payload.get("nfts", []), chain

        if response.status_code in (400, 404):
            last_error = RuntimeError(
                "OpenSea API returned "
                f"{response.status_code}: "
                f"{response.text[:200]}"
            )
            continue

        response.raise_for_status()

    if last_error:
        raise last_error

    raise RuntimeError(
        "NFT保有状況を確認できませんでした。"
    )


# ==================================================
# 共通データ読み込み
# ==================================================

try:
    market = get_market_data()
    game = load_game()

    game = update_game_once_per_day(
        game,
        market,
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

st.title("🐱 Nemo Garden")

st.caption(
    "現実の仮想通貨市場とつながる、"
    "ねもちゃんの小さな世界"
)


# ==================================================
# 5タブ
# ==================================================

(
    market_tab,
    fishing_tab,
    garden_tab,
    shop_tab,
    secret_tab,
) = st.tabs(
    [
        "📈 市場・星待館",
        "🎣 釣り場",
        "🌸 庭園",
        "🛍️ 売店",
        "🌙 秘密の庭",
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
            f"{market['bitcoin']['jpy_24h_change']:+.2f}%",
        )

    with eth:
        st.metric(
            "ETH",
            f"¥{market['ethereum']['jpy']:,.0f}",
            f"{market['ethereum']['jpy_24h_change']:+.2f}%",
        )

    with sol:
        st.metric(
            "SOL",
            f"¥{market['solana']['jpy']:,.0f}",
            f"{market['solana']['jpy_24h_change']:+.2f}%",
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
            f"{game['guests']}人",
        )

        st.metric(
            "💰 累計売上",
            f"{game['total_sales']:,} G",
        )

    with right:
        st.metric(
            "🐱 元気度",
            f"{game['nemo_energy']} / 100",
        )

        st.metric(
            "📅 最終更新",
            game["last_update"],
        )

    try:
        inventory_for_balance = get_inventory()

        available_coins = get_available_coins(
            game,
            inventory_for_balance,
        )

        st.metric(
            "👛 使えるG",
            f"{available_coins:,} G",
        )

    except Exception:
        pass

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
        "🎁 売店には旅の道具や"
        "星待館のお土産が並んでいます。"
    )


# ==================================================
# 釣り場
# ==================================================

with fishing_tab:
    st.header("🎣 星の釣り場")

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

    if today_catch is None:
        st.info(
            "🐾 今日はまだ釣りをしていません。"
        )

        if st.button(
            "🎣 今日の釣りをする",
            use_container_width=True,
        ):
            try:
                catch_fish()

                st.success(
                    "ねもちゃんが何か釣った！"
                )

                st.rerun()

            except Exception as e:
                st.error(
                    "釣りに失敗しました。"
                )
                st.code(str(e))

    else:
        st.success(
            "🐱 今日はもう釣りました！"
        )

        st.subheader("🐟 今日の釣果")

        st.metric(
            "魚",
            today_catch["fish_name"],
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "レア度",
                today_catch["rarity"],
            )

        with col2:
            st.metric(
                "サイズ",
                f'{today_catch["size_cm"]} cm',
            )

        st.write(
            f'💬 {today_catch["note"]}'
        )

        st.caption(
            "また明日、釣りに来よう。"
        )

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

    st.divider()
    st.subheader("📚 魚図鑑")

    caught_names = {
        catch["fish_name"]
        for catch in recent
    }

    discovered = sum(
        1
        for fish in FISH_LIST
        if fish["name"] in caught_names
    )

    st.write(
        f"**{discovered} / "
        f"{len(FISH_LIST)} 種類発見**"
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


# ==================================================
# 庭園
# ==================================================

with garden_tab:
    st.header("🌸 ねもちゃん庭園")

    st.write(
        "星待館の小さなお庭。"
    )

    st.write(
        "1日1回お世話すると、"
        "少しずつ植物が育ちます。"
    )

    try:
        garden = load_garden()
        garden_log = get_garden_log()

    except Exception as e:
        st.error(
            "庭園の読み込みに失敗しました。"
        )
        st.code(str(e))
        st.stop()

    st.subheader("🪴 今日のお庭")
    st.info(
        garden_stage_text(garden)
    )

    if garden.get("plant_name"):
        plant_meta = get_plant_meta(
            garden["plant_name"]
        )

        st.write(
            f"育てている植物："
            f"**{plant_meta['emoji']} "
            f"{garden['plant_name']}**"
        )

        st.write(
            f"レア度："
            f"**{garden.get('rarity', '')}**"
        )

        stage = int(
            garden.get(
                "growth_stage",
                0,
            )
        )

        if stage == 1:
            st.progress(33)
        elif stage == 2:
            st.progress(66)
        elif stage >= 3:
            st.progress(100)

    already_tended = (
        garden.get("last_tended_date")
        == today_str()
    )

    if already_tended:
        st.success(
            "🐱 今日はもうお庭のお世話をしました！"
        )
        st.caption(
            "また明日見に来よう。"
        )

    else:
        if not garden.get("plant_name"):
            button_text = "🌱 種を植える"

        elif int(
            garden.get(
                "growth_stage",
                0,
            )
        ) >= 3:
            button_text = (
                "🌱 次の植物を育てる"
            )

        else:
            button_text = (
                "💧 今日のお世話をする"
            )

        if st.button(
            button_text,
            use_container_width=True,
        ):
            try:
                updated_garden, result = (
                    tend_garden(garden)
                )

                if result == "planted":
                    st.success(
                        "🌱 ねもちゃんが新しい種を植えました！"
                    )

                elif result == "grown":
                    st.success(
                        "🌿 植物が少し大きくなりました！"
                    )

                elif result == "bloomed":
                    st.balloons()
                    st.success(
                        f"🌸 "
                        f"{updated_garden['plant_name']}"
                        f"が咲きました！"
                    )

                st.rerun()

            except Exception as e:
                st.error(
                    "お庭のお世話に失敗しました。"
                )
                st.code(str(e))

    st.divider()
    st.subheader(
        "🌺 これまで咲いた花"
    )

    if garden_log:
        for bloom in garden_log[:5]:
            meta = get_plant_meta(
                bloom["plant_name"]
            )

            st.write(
                f'**{bloom["bloom_date"]}**　'
                f'{meta["emoji"]} '
                f'{bloom["plant_name"]}　'
                f'{bloom["rarity"]}'
            )

    else:
        st.caption(
            "まだ花は咲いていません。"
        )

    st.divider()
    st.subheader("📗 植物図鑑")

    bloomed_names = {
        bloom["plant_name"]
        for bloom in garden_log
    }

    discovered_plants = sum(
        1
        for plant in PLANT_LIST
        if plant["name"] in bloomed_names
    )

    st.write(
        f"**{discovered_plants} / "
        f"{len(PLANT_LIST)} 種類発見**"
    )

    for plant in PLANT_LIST:
        if plant["name"] in bloomed_names:
            st.write(
                f'{plant["emoji"]} '
                f'**{plant["name"]}** '
                f'{plant["rarity"]}'
            )
        else:
            st.write(
                "❓ **？？？**"
            )


# ==================================================
# 売店
# ==================================================

with shop_tab:
    st.header("🛍️ 星待館の売店")

    st.write(
        "旅の道具や、"
        "星待館のお土産が並んでいます。"
    )

    try:
        inventory = get_inventory()

    except Exception as e:
        st.error(
            "売店の読み込みに失敗しました。"
        )
        st.code(str(e))
        st.stop()

    available_coins = get_available_coins(
        game,
        inventory,
    )

    st.metric(
        "👛 使えるG",
        f"{available_coins:,} G",
    )

    st.caption(
        "星待館が毎日稼いだGを、"
        "売店で使えます。"
    )

    st.divider()
    st.subheader("🏪 商品")

    owned_keys = {
        row["item_key"]
        for row in inventory
    }

    for item in SHOP_ITEMS:
        st.markdown(
            f"### {item['emoji']} "
            f"{item['name']}"
        )

        st.write(
            item["description"]
        )

        st.write(
            f"**{item['price']:,} G**"
        )

        if item["key"] in owned_keys:
            st.success(
                "✅ 購入済み"
            )

        elif available_coins < item["price"]:
            st.button(
                "Gが足りません",
                key="poor_" + item["key"],
                disabled=True,
                use_container_width=True,
            )

        else:
            if st.button(
                f"{item['price']:,}Gで購入",
                key="buy_" + item["key"],
                use_container_width=True,
            ):
                try:
                    result = buy_item(
                        item,
                        game,
                        inventory,
                    )

                    if result == "purchased":
                        st.success(
                            f"{item['name']}を買いました！"
                        )
                        st.rerun()

                    elif result == "owned":
                        st.info(
                            "すでに持っています。"
                        )

                    elif result == "not_enough":
                        st.warning(
                            "Gが足りません。"
                        )

                except Exception as e:
                    st.error(
                        "購入に失敗しました。"
                    )
                    st.code(str(e))

        st.divider()

    st.subheader("🎒 持ち物")

    if inventory:
        for owned in inventory:
            matching = next(
                (
                    item
                    for item in SHOP_ITEMS
                    if item["key"]
                    == owned["item_key"]
                ),
                None,
            )

            if matching:
                st.write(
                    f'{matching["emoji"]} '
                    f'**{matching["name"]}**'
                )

            else:
                st.write(
                    f'🎁 '
                    f'**{owned["item_name"]}**'
                )

    else:
        st.caption(
            "まだ何も持っていません。"
        )


# ==================================================
# 秘密の庭
# ==================================================

with secret_tab:
    st.header("🌙 秘密の庭")

    st.caption(
        "NemoCollection2023 holder gate — β版"
    )

    st.write(
        "NemoCollection2023を持っている"
        "ウォレットだけが入れる、"
        "ねもちゃんの小さな隠し場所です。"
    )

    st.info(
        "このβ版では公開ウォレットアドレスだけを使って"
        "NFT保有状況を確認します。"
        "署名・送金・ガス代は発生しません。"
    )

    wallet_address = st.text_input(
        "ウォレットアドレス",
        placeholder="0x...",
        help=(
            "MetaMaskの公開ウォレットアドレスを入力してください。"
            "シークレットリカバリーフレーズや秘密鍵は"
            "絶対に入力しないでください。"
        ),
        key="nemo_holder_wallet",
    ).strip()

    check_clicked = st.button(
        "🔎 Nemo NFTを確認",
        type="primary",
        use_container_width=True,
        key="nemo_holder_check",
    )

    if check_clicked:
        if not ADDRESS_RE.fullmatch(
            wallet_address
        ):
            st.error(
                "ウォレットアドレスの形式を確認してください。"
                "0xから始まる42文字の公開アドレスを入力します。"
            )

        else:
            with st.spinner(
                "Polygon上のNemoCollection2023を確認しています…"
            ):
                try:
                    nfts, detected_chain = get_nemo_nfts(
                        wallet_address
                    )

                except Exception as exc:
                    st.session_state.pop(
                        "nemo_holder",
                        None,
                    )
                    st.session_state.pop(
                        "nemo_holder_nfts",
                        None,
                    )

                    st.error(
                        "NFT保有状況を確認できませんでした。"
                        "少し時間を置いてもう一度試してください。"
                    )

                    st.caption(
                        f"開発用エラー: {exc}"
                    )

                else:
                    st.session_state[
                        "nemo_holder"
                    ] = bool(nfts)

                    st.session_state[
                        "nemo_holder_nfts"
                    ] = nfts

                    st.session_state[
                        "nemo_holder_address"
                    ] = wallet_address

                    st.session_state[
                        "nemo_holder_chain"
                    ] = detected_chain

    if st.session_state.get(
        "nemo_holder"
    ):
        nfts = st.session_state.get(
            "nemo_holder_nfts",
            [],
        )

        st.success(
            "🔓 Nemo Holder ✓  秘密の庭がひらきました。"
        )

        st.markdown(
            "## おかえりなさい。"
        )

        st.write(
            "ここは、"
            "あなたとねもの記念の場所です。"
        )

        if nfts:
            first_nft = nfts[0]

            image_url = (
                first_nft.get("image_url")
                or first_nft.get(
                    "display_image_url"
                )
            )

            nft_name = (
                first_nft.get("name")
                or "NemoCollection2023"
            )

            if image_url:
                st.image(
                    image_url,
                    width=300,
                )

            st.markdown(
                f"**確認できたNFT：{nft_name}**"
            )

            if len(nfts) > 1:
                st.caption(
                    f"今回の取得範囲では "
                    f"{len(nfts)} 点のNemo NFTを確認できました。"
                )

        st.divider()
        st.markdown(
            "### 🌸 Holder Only"
        )

        st.info(
            "ねもを見つけてくれて、ありがとう。  \n"
            "この一枚の出会いが、  \n"
            "あなたの小さな物語になりますように。"
        )

        st.markdown(
            "[NemoCollection2023をOpenSeaで見る]"
            "(https://opensea.io/collection/nemocollection2023)"
        )

    elif st.session_state.get(
        "nemo_holder"
    ) is False:
        st.warning(
            "このウォレットでは"
            "NemoCollection2023を確認できませんでした。"
        )

        st.caption(
            "別のウォレットにNFTがある場合は、"
            "その公開アドレスで確認してください。"
        )


# ==================================================
# 共通フッター
# ==================================================

st.divider()

now = datetime.now(TOKYO)

st.caption(
    f"市場データ取得："
    f"{now.strftime('%Y/%m/%d %H:%M')}"
)

st.caption(
    "星待館・釣り場・庭園・売店は、"
    "みんなで同じ世界を共有しています。"
)
