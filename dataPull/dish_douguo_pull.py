# step1_douguo.py
import requests, csv, time, random
from lxml import etree

BASE_URL = "https://www.douguo.com/caipu/{}/0/{}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_page(page, cuisine):
    url = BASE_URL.format(cuisine, page * 20)
    r = requests.get(url, headers=HEADERS, timeout=10).text
    doc = etree.HTML(r)
    items = doc.xpath('//li[@class="clearfix"]')
    rows = []
    for i in items:
        title = i.xpath('./a/@title')[0]
        href = "https://www.douguo.com" + i.xpath('./div/a/@href')[0]
        peiliao = i.xpath('./div/p/text()')[0]      # 主料
        cook_time = i.xpath('.//span[@class="time"]/text()')[0].replace('分钟', '') or 0
        rate = i.xpath('.//span[@class="score"]/text()')[0].replace('分', '') or 0
        rows.append([title, href, peiliao, int(cook_time), float(rate)])
    return rows

def main():
    cuisines = ["川菜", "粤菜", "东北菜", "鲁菜", "浙菜"]
    with open("recipes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "url", "ingredients", "cook_time", "rating"])
        for c in cuisines:
            for p in range(50):  # 每菜系爬 50 页
                rows = fetch_page(p, c)
                if not rows:
                    break
                writer.writerows(rows)
                time.sleep(random.uniform(1, 2))
                print(f"{c} 第{p+1}页完成")

if __name__ == "__main__":
    main()