import requests  
from bs4 import BeautifulSoup  
from datetime import datetime, timezone  
from dateutil import parser  
import re
import sys

STATUS_LABELS = {
    "launched": "一般提供",
    "in preview": "パブリックプレビュー",
    "in development": "開発中",
}

AVAILABILITY_LABELS = {
    "general availability": "一般提供",
    "preview": "パブリックプレビュー",
    "public preview": "パブリックプレビュー",
    "private preview": "プライベートプレビュー",
    "retirement": "リタイアメント",
}

TITLE_PREFIX_LABELS = (
    ("Generally Available", "一般提供"),
    ("General Availability", "一般提供"),
    ("Public Preview", "パブリックプレビュー"),
    ("Private Preview", "プライベートプレビュー"),
    ("In Development", "開発中"),
    ("Retirement", "リタイアメント"),
    ("Preview", "パブリックプレビュー"),
    ("GA", "一般提供"),
)

EDITORIAL_PREFIXES = ("Announcing", "New")
REVIEW_CATEGORY_LABEL = "要確認"
PREVIEW_LABELS = {"パブリックプレビュー", "プライベートプレビュー"}


def extract_title_signals(raw_title):
    """タイトルを表示用本文、接頭辞、ライフサイクル区分に分ける。"""
    title = raw_title.lstrip("\ufeff\u200b").strip()

    for prefix, label in TITLE_PREFIX_LABELS:
        match = re.match(rf"^{re.escape(prefix)}\s*:\s*", title, re.IGNORECASE)
        if match:
            return title[match.end():].strip(), prefix, label

    for prefix in EDITORIAL_PREFIXES:
        match = re.match(rf"^{re.escape(prefix)}\s*:\s*", title, re.IGNORECASE)
        if match:
            displayed_title = (
                title if prefix == "Announcing" else title[match.end():].strip()
            )
            return displayed_title, prefix, None

    return title, None, None


def get_availability_signals(item):
    rings = []
    labels = []

    for availability in item.get("availabilities") or []:
        ring = (availability.get("ring") or "").strip()
        if not ring:
            continue

        rings.append(ring)
        label = AVAILABILITY_LABELS.get(ring.casefold())
        if label and label not in labels:
            labels.append(label)

    return rings, labels


def labels_are_compatible(title_label, status_label):
    if title_label == status_label:
        return True

    return status_label == "パブリックプレビュー" and title_label in PREVIEW_LABELS


def availability_supports_label(
    label,
    availability_labels,
    include_private_preview=False,
):
    labels = set(availability_labels)
    if label == "一般提供":
        return "一般提供" in labels
    if label == "パブリックプレビュー":
        supported_preview_labels = {"パブリックプレビュー"}
        if include_private_preview:
            supported_preview_labels.add("プライベートプレビュー")
        return (
            bool(labels & supported_preview_labels)
            and "一般提供" not in labels
        )
    if label == "プライベートプレビュー":
        return (
            "プライベートプレビュー" in labels
            and "パブリックプレビュー" not in labels
            and "一般提供" not in labels
        )
    if label == "開発中":
        return "開発中" in labels
    if label == "リタイアメント":
        return "リタイアメント" in labels
    return False


def normalize_update_status(item):
    """APIの複数シグナルから表示区分を決め、曖昧な場合は確認情報を返す。"""
    title, title_prefix, title_label = extract_title_signals(
        item.get("title", "")
    )
    raw_status = (item.get("status") or "").strip()
    status_label = STATUS_LABELS.get(raw_status.casefold())
    rings, availability_labels = get_availability_signals(item)
    tags = item.get("tags") or []
    tag_names = {tag.casefold() for tag in tags}

    retirement_tag = "retirements" in tag_names
    announcement_signal = (
        (title_prefix or "").casefold() == "announcing"
        or "announcement" in tag_names
    )

    category_label = None
    candidate_label = None
    review_reason = None

    if title_label:
        if status_label and not labels_are_compatible(
            title_label, status_label
        ):
            candidate_label = title_label
            review_reason = "title prefix and API status disagree"
        elif availability_labels and not availability_supports_label(
            title_label, availability_labels
        ):
            candidate_label = title_label
            review_reason = "title prefix and availability disagree"
        else:
            category_label = title_label
    elif announcement_signal:
        if status_label and availability_supports_label(
            status_label,
            availability_labels,
            include_private_preview=True,
        ):
            category_label = status_label
            if (
                status_label == "パブリックプレビュー"
                and set(availability_labels) == {"プライベートプレビュー"}
            ):
                category_label = "プライベートプレビュー"
        else:
            candidate_label = status_label
            review_reason = "announcement lifecycle is not corroborated"
    elif status_label:
        if availability_labels and not availability_supports_label(
            status_label,
            availability_labels,
            include_private_preview=True,
        ):
            candidate_label = status_label
            review_reason = "API status and availability disagree"
        else:
            category_label = status_label
            if (
                status_label == "パブリックプレビュー"
                and set(availability_labels) == {"プライベートプレビュー"}
            ):
                category_label = "プライベートプレビュー"
    elif len(availability_labels) == 1:
        category_label = availability_labels[0]
    elif retirement_tag:
        category_label = "リタイアメント"
    else:
        review_reason = "no lifecycle category was found"

    review = None
    if review_reason:
        review = {
            "reason": review_reason,
            "status": raw_status,
            "title_prefix": title_prefix or "",
            "availability": rings,
            "tags": tags,
            "id": str(item.get("id") or ""),
            "candidate": candidate_label or "",
        }

    return {
        "category": category_label or REVIEW_CATEGORY_LABEL,
        "title": title,
        "review": review,
    }


def format_status_review(review):
    if not review:
        return ""

    availability = ", ".join(review["availability"]) or "(none)"
    tags = ", ".join(review["tags"]) or "(none)"
    return (
        "<!-- status-review\n"
        f"reason: {review['reason']}\n"
        f"status: {review['status'] or '(none)'}\n"
        f"title-prefix: {review['title_prefix'] or '(none)'}\n"
        f"availability: {availability}\n"
        f"tags: {tags}\n"
        f"id: {review['id'] or '(none)'}\n"
        f"candidate: {review['candidate'] or '(none)'}\n"
        "-->\n"
    )


def fetch_update_items(base_url, headers, page_size, filter_date):
    """ページを順にたどり、フィルター日付より古い更新に到達するまで項目を返す。"""
    skip = 0
    while True:
        response = requests.get(base_url.format(skip=skip), headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"エラー: データを取得できませんでした。ステータスコード: {response.status_code}")
            print(f"レスポンスの内容:\n{response.text}")
            return

        try:
            data = response.json()
        except ValueError:
            print("エラー: レスポンスから JSON をデコードできませんでした。")
            print(f"レスポンスの内容:\n{response.text}")
            return

        items = data.get("value", [])
        if not items:
            return

        yield from items

        last_modified = items[-1].get("modified", "")
        if last_modified and parser.isoparse(last_modified) < filter_date:
            return

        skip += page_size


def main():  
    if len(sys.argv) < 2:  
        print("エラー: 日付を引数として指定してください。形式: YYYY-MM-DD")  
        return  

    try:  
        filter_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").replace(tzinfo=timezone.utc)  
        filter_date_str = filter_date.strftime("%Y%m%d")  
    except ValueError:  
        print("エラー: 日付の形式が正しくありません。形式: YYYY-MM-DD")  
        return  

    page_size = 50
    base_url = f"https://www.microsoft.com/releasecommunications/api/v2/azure?$count=true&includeFacets=true&top={page_size}&skip={{skip}}&orderby=modified%20desc"
    headers = {  
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',  
        'Accept': 'application/json, text/plain, */*',  
        'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',  
        'Referer': 'https://www.microsoft.com/ja-jp/releasecommunications/azure',  
        'Origin': 'https://www.microsoft.com'  
    }  
 
    output_filename = f"azure_update_{filter_date_str}_{datetime.now().strftime('%Y%m%d')}.md"
    with open(output_filename, "w", encoding="utf-8") as f:  # ファイルを最初に開く
        for item in fetch_update_items(base_url, headers, page_size, filter_date):  
            modified_date = item.get("modified", "")  
            if modified_date:  
                try:  
                    date_obj = parser.isoparse(modified_date)
                    if date_obj < filter_date:  
                        continue  # フィルター日付より古い場合はスキップ  
                    date_str = date_obj.strftime("%Y-%m-%d")  
                except Exception as e:  
                    print(f"エラー: 日付のパースに失敗しました。詳細: {e}")  
                    date_str = "不明"  
            else:  
                date_str = "不明"  
     
            status_resolution = normalize_update_status(item)
            slide_title = (
                f"# {status_resolution['category']}: "
                f"{status_resolution['title']}"
            )
            status_review = format_status_review(status_resolution["review"])
     
            # 更新対象機能の抽出  
            products = item.get("products", [])  
            features = ", ".join(products)  
            features_text = f"Azure {features}"  
     
            # 更新内容の抽出（HTMLタグを除去）  
            description_html = item.get("description", "")  
            soup = BeautifulSoup(description_html, 'html.parser')  
            description_text = soup.get_text().strip()  
     
            # 参考リンクの抽出  
            reference_links = []  
            for link in soup.find_all('a', href=True):  
                reference_links.append(link['href'])  
     
            # スライドの内容を構築  
            slide_content = f"""{slide_title}
{status_review}
     
    ## 更新対象機能  
    {features_text}  
     
    ## 更新日付  
    {date_str}  
     
    ## 更新内容  
    {description_text}  
     
    ## 参考リンク  
    """  
            if reference_links:  
                for link in reference_links:  
                    slide_content += f" - {link}\n"  
            else:  
                slide_content += " - なし\n"  
     
            # スライドを出力  
            print(slide_content)  
            print("="*50)  
     
            # 上記の内容をファイルに出力（引数日付_今日の日付つきファイル名）  
            f.write(slide_content)  
            f.write("="*50)  
            f.write("\n")  
  
if __name__ == "__main__":  
    main()
