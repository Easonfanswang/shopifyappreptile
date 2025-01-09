import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import glob
import time
import subprocess


def run_scraper():
    print("未找到CSV文件，正在运行 scraper.py...")
    try:
        subprocess.run(["python", "scraper.py"], check=True)
        print("scraper.py 运行完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"运行 scraper.py 时出错: {e}")
        return False


def get_latest_csv(prefix="shopify_apps_", silent=False):
    csv_files = glob.glob(f"{prefix}*.csv")
    if not csv_files:
        if not silent:
            print(f"没有找到前缀为 {prefix} 的CSV文件")
            # 运行 scraper.py
            if run_scraper():
                # 重新检查CSV文件
                csv_files = glob.glob(f"{prefix}*.csv")
                if not csv_files:
                    print("即使运行了 scraper.py 后仍未找到CSV文件")
                    return None
            else:
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
    errors = []  # 存储错误信息
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    max_retries = 1  # 最大重试次数
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    total_items = batch_size if batch_size else len(df)

    for index, row in df.iterrows():
        if batch_size and index >= batch_size:
            break

        url = row["app_handle"]
        retry_count = 0
        success = False

        while retry_count < max_retries and not success:
            try:
                print(
                    f"正在处理 {index + 1}/{total_items} - {url} (第 {retry_count + 1} 次尝试)"
                )

                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    field_errors = []  # 记录每个字段的错误

                    data = {
                        "url": url,
                        "title": None,
                        "rating": None,
                        "reviews_count": None,
                        "main_description": None,
                        "detailed_description": None,
                        "detail_points": None,
                        "category": None,
                        "release_date": None,
                        "website": None,  # 新增官网字段
                        "complete_information": True,
                    }

                    incomplete_information = soup.find(
                        "div",
                        {
                            "class": "banner tw-bg-canvas-accent-orange tw-border-stroke-accent-orange tw-text-fg-accent-orange tw-py-4 lg:tw-py-8"
                        },
                    )
                    data["complete_information"] = (
                        False if incomplete_information else True
                    )

                    if data["complete_information"]:
                        # 获取标题
                        try:
                            title = soup.find(
                                "h1",
                                {
                                    "class": "tw-text-heading-lg tw-whitespace-normal tw-hyphens tw-text-balance -tw-my-xs"
                                },
                            )
                            data["title"] = title.text.strip() if title else None
                            if not data["title"]:
                                field_errors.append(
                                    {"field": "title", "error": "标题未找到"}
                                )
                        except Exception as e:
                            field_errors.append({"field": "title", "error": str(e)})

                        # 获取评分和评论
                        try:
                            rating_section = soup.find(
                                "dd",
                                {
                                    "class": "tw-flex tw-items-center tw-gap-2xs tw-text-body-sm"
                                },
                            )
                            if rating_section:
                                rating_span = rating_section.find("span")
                                data["rating"] = (
                                    rating_span.text.strip() if rating_span else None
                                )
                                if not data["rating"]:
                                    field_errors.append(
                                        {"field": "rating", "error": "评分未找到"}
                                    )
                                try:
                                    review_link = rating_section.find_all("span")[2]
                                    if review_link.find("a"):
                                        reviews_text = review_link.text.strip()
                                        data["reviews_count"] = (
                                            reviews_text.strip("()")
                                            .replace(",", "")
                                            .strip()
                                        )
                                    elif review_link:
                                        data["reviews_count"] = 0
                                    else:
                                        field_errors.append(
                                            {
                                                "field": "reviews_count",
                                                "error": "评论数未找到",
                                            }
                                        )
                                except Exception as e:
                                    field_errors.append(
                                        {"field": "reviews_count", "error": str(e)}
                                    )
                        except Exception as e:
                            field_errors.append(
                                {"field": "rating_section", "error": str(e)}
                            )

                        # 获取主要描述
                        try:
                            main_desc = soup.find(
                                "h2", {"class": "tw-text-heading-lg tw-text-pretty"}
                            )
                            data["main_description"] = (
                                main_desc.text.strip() if main_desc else None
                            )
                            if not data["main_description"]:
                                field_errors.append(
                                    {
                                        "field": "main_description",
                                        "error": "主要描述未找到",
                                    }
                                )
                        except Exception as e:
                            field_errors.append(
                                {"field": "main_description", "error": str(e)}
                            )

                        # 获取详细描述
                        try:
                            detailed_desc = soup.find(
                                "p",
                                {
                                    "class": "tw-hidden lg:tw-block tw-text-body-md tw-text-fg-secondary"
                                },
                            )
                            data["detailed_description"] = (
                                detailed_desc.text.strip() if detailed_desc else None
                            )
                            if not data["detailed_description"]:
                                field_errors.append(
                                    {
                                        "field": "detailed_description",
                                        "error": "详细描述未找到",
                                    }
                                )
                        except Exception as e:
                            field_errors.append(
                                {"field": "detailed_description", "error": str(e)}
                            )

                        # 获取详细点
                        try:
                            detail_elements = soup.find_all(
                                "li",
                                {
                                    "class": "tw-text-body-md tw-text-fg-secondary tw-mb-xs"
                                },
                            )
                            if detail_elements:
                                data["detail_points"] = "|".join(
                                    [
                                        element.text.strip()
                                        for element in detail_elements
                                    ]
                                )
                            else:
                                field_errors.append(
                                    {
                                        "field": "detail_points",
                                        "error": "详细点列表未找到",
                                    }
                                )
                        except Exception as e:
                            field_errors.append(
                                {"field": "detail_points", "error": str(e)}
                            )
                            
                        # 获取分类
                        try:
                            category_divs = soup.find_all(
                                "div",
                                {"class": "tw-flex tw-justify-between tw-mb-xl"}
                            )
                            if category_divs:
                                categories = []
                                for div in category_divs:
                                    a_tags = div.find_all('a')
                                    if a_tags:
                                        categories.extend([a.text.strip() for a in a_tags])
                                data["category"] = "|".join(categories) if categories else None
                            else:
                                field_errors.append({
                                    "field": "category",
                                    "error": "类目未找到",
                                })
                        except Exception as e:
                            field_errors.append(
                                {"field": "category", "error": str(e)}
                            )

                        # 获取发布日期
                        try:
                            release_date = soup.find(
                                "p",
                                {
                                    "class": "tw-col-span-full sm:tw-col-span-3 tw-text-fg-secondary tw-text-body-md"
                                },
                            )
                            if release_date:
                                # 分割文本并只保留日期部分
                                date_text = release_date.text.split('·')[0].strip()
                                # 将中文年月日替换为标准格式
                                date_text = date_text.replace('年', '-').replace('月', '-').replace('日', '')
                                # 转换为日期对象并格式化为 YYYY-MM-DD 格式
                                from datetime import datetime
                                date_obj = datetime.strptime(date_text, '%Y-%m-%d')
                                data["release_date"] = date_obj.strftime('%Y-%m-%d')
                            else:
                                field_errors.append({
                                    "field": "release_date",
                                    "error": "发布日期没找到",
                                })
                        except Exception as e:
                            field_errors.append(
                                {"field": "release_date", "error": str(e)}
                            )

                        # 获取官网
                        try:
                            website_link = soup.find("a", string="网站")
                            data["website"] = (
                                website_link["href"] if website_link else None
                            )
                        except Exception:
                            pass  # 如果没有找到网站链接，静默失败

                    # 如果有字段错误且是最后一次重试
                    if field_errors and retry_count == max_retries - 1:
                        for error in field_errors:
                            errors.append(
                                {
                                    "url": url,
                                    "field": error["field"],
                                    "error_message": error["error"],
                                }
                            )

                    # 如果所有必需字段都有值，则认为成功
                    if (
                        data["title"]
                        and data["rating"]
                        and data["main_description"]
                        and data["detailed_description"]
                        and data["detail_points"]
                        and data["category"]
                        and data["reviews_count"]
                        and data["release_date"]
                        and data["url"]
                        or incomplete_information
                    ):
                        results.append(data)
                        success = True
                        print(f"成功获取数据: {data['title']}")

                else:
                    if retry_count == max_retries - 1:
                        errors.append(
                            {
                                "url": url,
                                "field": "http_request",
                                "error_message": f"HTTP错误: {response.status_code}",
                            }
                        )

            except Exception as e:
                if retry_count == max_retries - 1:
                    errors.append(
                        {
                            "url": url,
                            "field": "request",
                            "error_message": f"请求失败: {str(e)}",
                        }
                    )

            if not success:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"重试 {retry_count}/{max_retries}")
                    time.sleep(delay * 2)

            time.sleep(delay)

    # 保存结果
    if results:
        output_file = f"app_titles_{timestamp}.csv"
        output_df = pd.DataFrame(results)
        output_df.to_csv(output_file, index=False, encoding="utf-8-sig")
        print(f"结果已保存到: {output_file}")
        print(f"总记录数: {len(output_df)}")

    # 保存错误记录
    if errors:
        error_file = f"scraping_errors_{timestamp}.csv"
        error_df = pd.DataFrame(errors)
        error_df.to_csv(error_file, index=False, encoding="utf-8-sig")
        print(f"错误记录已保存到: {error_file}")
        print(f"错误数量: {len(errors)}")


if __name__ == "__main__":
    scrape_app_details(delay=0.5)
