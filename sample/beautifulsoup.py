import requests
from bs4 import BeautifulSoup

# HTTP Get request
req = requests.get('http://www.yes24.com/24/Category/Display/001001003022004?ParamSortTp=04')

# Get HTML
html = req.text

# Convert html to python object by BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

goods_info = soup.find_all('div', class_='goods_info')

for goods in goods_info:
    title = goods.find(class_='goods_name').a.get_text().rstrip('\n')
    sub_title = goods.find(class_='gd_nameE').get_text().rstrip('\n')
    author = goods.find(class_='goods_auth').get_text().rstrip('\n')
    pub_date = goods.find(class_='goods_date').get_text().rstrip('\n')
    good_pub = goods.find(class_='goods_pub').get_text().rstrip('\n')
    total_title = title if sub_title is None else f'{title}: {sub_title}'
    print(total_title)
    print(author)
    print(pub_date)
    print(good_pub)
    print()
