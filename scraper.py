import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin
import os


class ShopifyAppScraper:
    def __init__(self):
        self.base_url = "https://apps.shopify.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.apps_data = []

    def get_app_listings(self, page=1):
        url = f"{self.base_url}/browse?page={page}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            return soup.find_all("div", {"data-app-card-handle-value": True})
        return []

    def extract_app_info(self, app_element):
        try:
            app_handle = app_element.get("data-app-card-handle-value")
            return {"app_handle": app_handle}
        except Exception as e:
            print(f"提取应用信息时出错: {e}")
            return None

    def scrape_apps(self, max_pages=1):
        for page in range(1, max_pages + 1):
            print(f"正在爬取第 {page} 页...")
            app_listings = self.get_app_listings(page)

            if not app_listings:
                break

            for app in app_listings:
                app_info = self.extract_app_info(app)
                if app_info:
                    self.apps_data.append(app_info)

            time.sleep(1)  # 添加延迟，避免请求过快

    def save_to_csv(self):
    # 添加调试信息
        print(f"收集到的数据数量: {len(self.apps_data)}")
        print(f"数据内容: {self.apps_data[:5]}")  
        
        # 使用当前脚本所在目录作为保存位置
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "shopify_apps.csv")
        
        df = pd.DataFrame(self.apps_data)
        df.to_csv(file_path, index=False, encoding="utf-8-sig")
        print(f"文件保存在: {file_path}")  # 打印保存位置


def main():
    scraper = ShopifyAppScraper()
    scraper.scrape_apps(max_pages=100)  # 设置要爬取的最大页数
    scraper.save_to_csv()


if __name__ == "__main__":
    main()
