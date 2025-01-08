import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin
import os
import time


class ShopifyAppScraper:
    def __init__(self):
        self.base_url = "https://apps.shopify.com/sitemap?locale=zh-CN"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.apps_data = []

    def get_app_listings(self):
        url = f"{self.base_url}"
        print(f"页面url: {url}")
        response = requests.get(url, headers=self.headers)
        print(f"页面状态码: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, features="xml")
            
            # 找到所有 loc 标签
            all_locs = soup.find_all("loc")
            
            # 过滤不需要的链接
            filtered_urls = []
            exclude_paths = ['categories', 'partner', 'stories', 'compare', 'collections', 'app-groups']
            
            for loc in all_locs:
                url = loc.text.strip()
                if url.startswith('https://apps.shopify.com/'):
                    # 检查URL是否包含需要排除的路径
                    path = url.split('apps.shopify.com/')[1]
                    if not any(exclude in path for exclude in exclude_paths):
                        filtered_urls.append(url)
            
            print(f"找到 {len(filtered_urls)} 个符合条件的应用URL")
            return filtered_urls
        return []

    def extract_app_info(self, link):
        try:
            app_handle = link
            return {"app_handle": app_handle}
        except Exception as e:
            print(f"提取链接时出错: {e}")
            return None

    def scrape_apps(self):
        app_listings = self.get_app_listings()
        print(f"当前数据: {app_listings}")

        if not app_listings:
            print(f"停止爬取")

        for link in app_listings:
            app_info = self.extract_app_info(link)
            if app_info:
                self.apps_data.append(app_info)


    def save_to_csv(self):
        # 添加调试信息
        print(f"收集到的数据数量: {len(self.apps_data)}")
        try:
            # 使用时间戳创建唯一文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            current_dir = os.path.dirname(os.path.abspath(__file__))
            file_path = os.path.join(current_dir, f"shopify_apps_{timestamp}.csv")

            df = pd.DataFrame(self.apps_data)
            df.to_csv(file_path, index=False, encoding="utf-8-sig")
            print(f"文件保存在: {file_path}")
        except Exception as e:
            print(f"保存文件时出错: {e}")
            # 尝试保存到临时目录
            import tempfile

            temp_path = os.path.join(
                tempfile.gettempdir(), f"shopify_apps_{timestamp}.csv"
            )
            df.to_csv(temp_path, index=False, encoding="utf-8-sig")
            print(f"文件已保存到临时目录: {temp_path}")


def main():
    scraper = ShopifyAppScraper()
    scraper.scrape_apps() 
    scraper.save_to_csv()


if __name__ == "__main__":
    main()
