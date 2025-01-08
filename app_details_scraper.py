import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import glob
import time


def get_latest_csv(prefix="shopify_apps_", silent=False):
    csv_files = glob.glob(f"{prefix}*.csv")
    if not csv_files:
        if not silent:
            print(f"没有找到前缀为 {prefix} 的CSV文件")
        return None
    latest_csv = max(csv_files, key=os.path.getmtime)
    if not silent:
        print(f"使用最新的CSV文件: {latest_csv}")
    return latest_csv


def scrape_app_details(batch_size=None, delay=0.5):
    csv_file = get_latest_csv()
    if not csv_file:
        return

    df = pd.read_csv(csv_file)
    results = []
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    total_items = batch_size if batch_size else len(df)
    
    for index, row in df.iterrows():
        if batch_size and index >= batch_size:
            print(f"已达到批次限制 ({batch_size})")
            break

        url = row["app_handle"]
        print(f"正在处理 {index + 1}/{total_items} - {url}")

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # 添加评分和评论数据爬取
                rating = None
                reviews_count = None

                rating_section = soup.find(
                    "dd",
                    {"class": "tw-flex tw-items-center tw-gap-2xs tw-text-body-sm"},
                )
                
                title = soup.find(
                    "h1",
                    {
                        "class": "tw-text-heading-lg tw-whitespace-normal tw-hyphens tw-text-balance -tw-my-xs"
                    },
                )
                if rating_section:
                    # 获取评分
                    rating_span = rating_section.find("span")
                    if rating_span:
                        rating = rating_span.text.strip()

                    # 获取评论数
                    review_link = rating_section.find_all("span")[2].find("a")
                    if review_link:
                        reviews_text = review_link.text.strip()
                        # 移除括号并转换为数字
                        cleaned_text = reviews_text.strip("()").replace(",", "")
                        reviews_count = cleaned_text if cleaned_text else "0"
                    else:
                        reviews_count = "0"
                if title:
                    title_text = title.text.strip()
                    results.append(
                        {
                            "url": url,
                            "title": title_text,
                            "rating": rating,
                            "reviews_count": reviews_count,
                            "timestamp": timestamp,
                        }
                    )
                    print(
                        f"找到标题: {title_text}, 评分: {rating}, 评论数: {reviews_count}"
                    )
                else:
                    print(f"未找到标题: {url}")
            else:
                print(f"请求失败 {url}: {response.status_code}")

            time.sleep(delay)

        except Exception as e:
            print(f"处理 {url} 时出错: {e}")

    # 保存结果
    if results:
        output_file = f"app_titles_{timestamp}.csv"
        output_df = pd.DataFrame(results)
        output_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"结果已保存到: {output_file}")
        print(f"总记录数: {len(output_df)}")
    else:
        print("没有找到任何标题")


if __name__ == "__main__":
    scrape_app_details(delay=2) 
