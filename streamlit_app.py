import streamlit as st
import requests
import random
from datetime import datetime

st.set_page_config(
    page_title="ねもちゃん市場",
    page_icon="🐱",
)

st.title("🐱 ねもちゃん市場")
st.caption("現実の仮想通貨市場とつながる、ねもちゃんの世界")

COINS = {
    "BTC": "btc_jpy",
    "ETH": "eth_jpy",
    "SOL": "sol_jpy",
}


@st.cache_data(ttl=60)
def get_market(pair):
    url = f"https://public.bitbank.cc/{pair}/ticker"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()["data"]

    price = float(data["last"])
    open_price = float(data["open"])

    change = ((price / open_price) - 1) * 100

    return price, change


def nemo_event(btc, eth, sol):

    events = []

    # BTC → 星待館の景気
    if btc >= 5:
        events.append("🏮 星待館は大繁盛！今日は満室です。")
    elif btc >= 2:
        events.append("🌸 星待館にお客さんが増えています。")
    elif btc <= -5:
        events.append("🌧️ 今日は客足が少なく、静かな星待館です。")
    else:
        events.append("♨️ 星待館は今日も平常運転です。")

    # ETH → ねもちゃん
    if eth >= 5:
        events.append("🐱 ねもちゃん絶好調。温泉街を走り回っています。")
    elif eth >= 2:
        events.append("🐱 ねもちゃんはご機嫌です。")
    elif eth <= -5:
        events.append("🛌 ねもちゃんは布団から出てきません。")
    elif eth <= -2:
        events.append("🐱💭 ねもちゃん、今日は少し元気がありません。")
    else:
        events.append("🐱 ねもちゃんはのんびり過ごしています。")

    # SOL → 売店・イベント
    if sol >= 7:
        events.append("🎆 SOL祭が始まりました！")
    elif sol >= 3:
        events.append(
            random.choice(
                [
                    "🍡 売店にSOLまんじゅうが入荷しました。",
                    "🎁 売店に謎の新商品が入荷しました。",
                    "🎵 ロビーで小さなイベントが始まりました。",
                ]
            )
        )
    elif sol <= -7:
        events.append("💥 売店が大混乱しています。")
    elif sol <= -3:
        events.append("📦 売店の商品が少し寂しくなっています。")
    else:
        events.append("🏪 売店はいつも通り営業中です。")

    return events


st.subheader("📈 今日の市場")

market = {}

try:
    for name, pair in COINS.items():
        price, change = get_market(pair)
        market[name] = change

        st.metric(
            label=name,
            value=f"¥{price:,.0f}",
            delta=f"{change:+.2f}%"
        )

    st.divider()

    st.subheader("♨️ 今日の星待館")

    events = nemo_event(
        market["BTC"],
        market["ETH"],
        market["SOL"],
    )

    for event in events:
        st.write(event)

    if all(x >= 2 for x in market.values()):
        st.success("🎆 SPECIAL EVENT：今夜、星待館で花火大会が開催されます！")

    elif all(x <= -2 for x in market.values()):
        st.warning("⚡ SPECIAL EVENT：市場が荒れています。星待館に嵐が近づいています……。")

    st.caption(
        "更新：" + datetime.now().strftime("%Y/%m/%d %H:%M")
    )

except Exception as e:
    st.error("市場データを取得できませんでした。")
    st.write(e)
