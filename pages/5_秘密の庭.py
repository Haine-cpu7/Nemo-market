import re

import requests
import streamlit as st


# ==================================================
# 基本設定
# ==================================================

st.set_page_config(
    page_title="ねもがーでん｜秘密の庭",
    page_icon="🌙",
    layout="centered",
)

COLLECTION_SLUG = "nemocollection2023"
OPENSEA_AUTH_URL = "https://api.opensea.io/api/v2/auth/keys"
OPENSEA_ACCOUNT_NFTS_URL = (
    "https://api.opensea.io/api/v2/chain/{chain}/account/{address}/nfts"
)

ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")


# ==================================================
# OpenSea API
# ==================================================

@st.cache_resource(ttl=6 * 24 * 60 * 60)
def get_opensea_api_key():
    """OpenSea API keyを取得する。

    Streamlit secrets に OPENSEA_API_KEY があればそれを優先。
    なければOpenSea公式のInstant API Keyを取得する。
    Instant keyは期限付きなので6日でキャッシュ更新する。
    """

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
        raise RuntimeError("OpenSea API keyを取得できませんでした。")

    return api_key


@st.cache_data(ttl=60, show_spinner=False)
def get_nemo_nfts(address):
    """指定ウォレットが保有するNemoCollection2023を取得する。"""

    api_key = get_opensea_api_key()
    headers = {
        "X-API-KEY": api_key,
        "Accept": "application/json",
    }

    # OpenSea側のチェーン識別子変更にも少し耐えられるようにする。
    chain_candidates = ("polygon", "matic")
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
                f"OpenSea API returned {response.status_code}: {response.text[:200]}"
            )
            continue

        response.raise_for_status()

    if last_error:
        raise last_error

    raise RuntimeError("NFT保有状況を確認できませんでした。")


# ==================================================
# UI
# ==================================================

st.title("🌙 秘密の庭")
st.caption("NemoCollection2023 holder gate — β版")

st.markdown(
    """
NemoCollection2023を持っているウォレットだけが入れる、ねもがーでんの小さな隠し場所です。

このβ版はまず**NFT保有判定そのものが正しく動くか**を確認するため、
ウォレットアドレスを入力してチェックします。NFTを移動したり、署名したり、
ガス代を払ったりする処理はありません。
"""
)

wallet_address = st.text_input(
    "ウォレットアドレス",
    placeholder="0x...",
    help=(
        "MetaMaskの公開ウォレットアドレスを入力してください。"
        "シークレットリカバリーフレーズや秘密鍵は絶対に入力しないでください。"
    ),
).strip()

check_clicked = st.button(
    "🔎 Nemo NFTを確認",
    type="primary",
    use_container_width=True,
)

if check_clicked:
    if not ADDRESS_RE.fullmatch(wallet_address):
        st.error(
            "ウォレットアドレスの形式を確認してください。"
            "0xから始まる42文字の公開アドレスを入力します。"
        )
    else:
        with st.spinner("Polygon上のNemoCollection2023を確認しています…"):
            try:
                nfts, detected_chain = get_nemo_nfts(wallet_address)
            except Exception as exc:
                st.session_state.pop("nemo_holder", None)
                st.session_state.pop("nemo_holder_nfts", None)
                st.error(
                    "NFT保有状況を確認できませんでした。"
                    "少し時間を置いてもう一度試してください。"
                )
                st.caption(f"開発用エラー: {exc}")
            else:
                st.session_state["nemo_holder"] = bool(nfts)
                st.session_state["nemo_holder_nfts"] = nfts
                st.session_state["nemo_holder_address"] = wallet_address
                st.session_state["nemo_holder_chain"] = detected_chain


if st.session_state.get("nemo_holder"):
    nfts = st.session_state.get("nemo_holder_nfts", [])

    st.success("🔓 Nemo Holder ✓  秘密の庭がひらきました。")
    st.markdown("## おかえりなさい。")
    st.write("2023年からねもちゃんを持っていてくれた人だけの場所です。")

    if nfts:
        first_nft = nfts[0]
        image_url = (
            first_nft.get("image_url")
            or first_nft.get("display_image_url")
        )
        nft_name = first_nft.get("name") or "NemoCollection2023"

        if image_url:
            st.image(image_url, width=300)

        st.markdown(f"**確認できたNFT：{nft_name}**")

        if len(nfts) > 1:
            st.caption(
                f"今回の取得範囲では {len(nfts)} 点のNemo NFTを確認できました。"
            )

    st.divider()
    st.markdown("### 🌸 Holder Only")
    st.info(
        "ここに、限定イラスト・古参称号・秘密のコレクション・"
        "専用会話などを追加していけます。"
    )

    st.markdown(
        "[NemoCollection2023をOpenSeaで見る]"
        "(https://opensea.io/collection/nemocollection2023)"
    )

elif st.session_state.get("nemo_holder") is False:
    st.warning(
        "このウォレットではNemoCollection2023を確認できませんでした。"
    )
    st.caption(
        "別のウォレットにNFTがある場合は、その公開アドレスで確認してください。"
    )


st.divider()
st.caption(
    "β版：次の段階でMetaMaskの「ウォレットを接続」ボタンと署名認証を追加し、"
    "アドレス手入力なしで入れる形にします。"
)
