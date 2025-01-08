# shopifyappreptile

dev commit：
python scraper.py //爬取所有应用链接，保存到 csv
python app_details_scraper.py //根据最新 csv 爬取应用数据，修改 app_details_scraper.py 项目中 scrape_app_details(batch_size=5, delay=2)中 batch_size 的值改变最大爬取数 delay 改变延迟，默认为 csv 长度和 0.5
