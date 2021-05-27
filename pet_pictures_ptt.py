"""
/PPT寵物版爬蟲程式/
/請使用button 輸入數字(int or str)來爬蟲 ：從第一頁開始往後爬的頁數 。 button皆為支援(子)方法/

purpose：輸入想要爬的頁數

輸入：輸入數字,想要爬取頁數
輸出：執行mianthread爬蟲程序

這裡分兩段，
第一段用PPT寵物版首頁的連結找出目前的頁數
第二段藉由button得到想要爬取的頁數，接著執行爬蟲程式

"""
def button(pages=2):
    import requests
    from bs4 import BeautifulSoup

    HOST = "https://www.ptt.cc"
    res = requests.get(HOST + "/bbs/Beauty/index.html", headers={"cookie": "over18=1;"})
    soup = BeautifulSoup(res.text, 'html.parser')
    buttons = soup.select('a.btn.wide')
    total_page = int(buttons[1]['href'].split('index')[1].split('.html')[0]) + 1

    page_to_crawl = int(pages) #決定要爬幾個頁數
    for page in range(total_page, total_page - page_to_crawl, -1):
        url = 'https://www.ptt.cc/bbs/Pet_Get/index{}.html'.format(page)
        mainthread(url)

        
"""
/主要執行爬蟲的程式碼在這/

這裡拆三段
1.取出寵物版首頁每篇文章的資訊，日期為當天最新的進行
2.為頭頁每篇文章做處理，抓取正確資訊並儲存圖片
3.json紀錄已更新的資訊

抓圖段落下個sleep 可調睡覺時間以防被擋

"""
def mainthread(url):
    import time
    from bs4 import BeautifulSoup

    articles= {}
    page = get_web_page(url)
    if page: #判別有無東西
        date = time.strftime('%m/%d').lstrip('0') #time抓當天時間-幾月幾號;但bbs時間回傳開頭會有0 所以加lstrip('0')把0幹掉
        articles = get_articles(page,date) #蒐集每篇文章的資訊


    #開始抓圖
    PPT_URL='https://www.ptt.cc'
    for article in articles:
        page = get_web_page(PPT_URL + article['href']) #抓回來的href沒有www.ptt.cc 自己加
        if page:
            img_urls = parse(page) #取出每篇的圖片集連結群
            save(img_urls,article['title']) #放入每篇圖片集的url跟標題,儲存圖片
            article['num_image'] = len(img_urls) #抓出圖片數量，紀錄用
            time.sleep(10) #設定睡覺時間 以免被擋掉


    import json #存成json檔紀錄
    with open('data.json','w',encoding='utf-8') as f:
        json.dump(articles,f,indent=2,sort_keys=True,ensure_ascii=False)
        
        
        
        
        
        
        
        
"""
purpos:塞入cookie確認是否滿18;判別requests是否成功

輸入:將要解析資訊的網址
輸出:回傳request的值，檔案已是text檔!

"""



def get_web_page(url):  
    from bs4 import BeautifulSoup
    import requests
    resp = requests.get(url=url,cookies={'over18':'1'}) #塞入cookie over18:1
    if resp.status_code != 200:  #用200判別連線是否正常
        print('Invalid url:',resp.url)
        return None
    else:
        return resp.text #記住回傳是text!
    
"""
purpose:抓取'該日'文章內容資訊：標題、網址、案讚數  ;目前這裡是寵物版，不是內容頁

輸入:寵物版已加上cookie的request與想抓取的日期
輸出:寵物版每個po文的內容資訊

1.find_all取得所有內文資訊,
2.判斷日期是否正確,
3.用find('div','nrec')取讚數,
4.用find('a')取出網址跟標題
5.取好的資訊放進articles , return出去

"""

def get_articles(dom, date):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(dom, 'html.parser')

    articles = []  # 儲存取得的文章資料
    divs = soup.find_all('div', 'r-ent') #'r-ent'就是每篇文章的附屬資訊
    for d in divs:
        #if d.find('div', 'date').string.strip() == date:  # 發文日期正確才繼續 ,這裡原寫法沒strip沒去掉空白，已更正
                # 取得推文數
        push_count = 0
        if d.find('div', 'nrec').string: #nrec→是按讚數
            try:  #轉換成功 
                push_count = int(d.find('div', 'nrec').string)  # 轉換字串為數字
            except ValueError:  # 若轉換失敗，不做任何事，push_count 保持為 0
                pass
            # 取得文章連結及標題
        if d.find('a'):  # 網址跟標題都在a裡面 如果a沒有代表已被版主刪除 用來判斷內文存在不存在
            href = d.find('a')['href'] #把a裡面 - href取出來
            title = d.find('a').string #把a整串全部抓下來
            articles.append({
                'title': title,
                'href': href,
                'push_count': push_count
            })
    return articles




"""
purpose:取出圖片網址群

輸入:當篇html碼
輸出:當篇的圖片網址

BeautifulSoup回傳的是text,
用find → id='main-contect'找出圖片的區塊,再用find_all找到所有 a的內容

for loop:從link['href'], href的class,用寫好的正規表示法抽出想要的圖片網址
img_urls:要回傳圖片網址集,裡面都是整理好的網址

"""
def parse(dom): #過濾出乾淨的圖片網址LIST
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(dom,'html.parser') #用html.parser引擎
    links = soup.find(id='main-content').find_all('a') #圖片的標籤
    img_urls = []
    for link in links:
        if re.match(r'^https?://(i.)?(m.)?imgur.com', link['href']): #正規表示法
            img_urls.append(link['href']) #每抽出一次新增到img_urls裡面
    return img_urls



"""
purpose:把檔案存進建好的路徑

輸入:存好的圖片群,圖片的標題群
輸出:資料夾,與存好在資歷夾的jpg檔案

dname:把標題名稱切乾淨
for loop:抓到的檔案url名稱不乾淨 要統一種格式才能下載

"""

def save(img_urls,title):  
    import os
    import urllib
    from datetime import date # 106.6.3
    today =date.today() #抓出當天日期 格式 2016-06-03  106.6.3
    if img_urls:
        try:
            if not title.strip().find('Re:') != -1:#去除會因為'Re:'命名而無法建資料夾的狀況
                title.strip().replace('Re:','')
            dname = title.strip() #標題旁邊去空白
            if 'All_picture' not in os.listdir(): #找尋看有無all_pitcure資料夾 106.6.3
                os.makedirs('All_picture')# 沒尋到就新建立一個 106.6.3
            if 'Everyday_pictures' not in os.listdir(): #找尋看有無all_pitcure資料夾 106.6.3
                os.makedirs('Everyday_pictures')# 沒尋到就新建立一個 106.6.3
            if str(today) not in os.listdir('All_picture'): #找尋看有無all_pitcure資料夾 106.6.3
                os.makedirs('All_picture\\'+str(today))# 沒尋到就新建立一個 106.6.3            
            if str(today) not in os.listdir('Everyday_pictures'): #找尋看有無當天日期資料夾 106.6.3
                os.makedirs('Everyday_pictures\\'+str(today))# 沒尋到就新建立一個 106.6.3
            os.makedirs('All_picture\\'+str(today)+'\\'+dname) #創建資料夾
            
            for img_url in img_urls: # 下載的時候必須是i.imgur.com  以下處理不是的
                if img_url.split('//')[1].startswith('m.'):  #如果開頭是 m.imgur.com  把m換成i.
                    img_url = img_url.replace('//m.','//i.')
                if not img_url.split('//')[1].startswith('i.'): #如果開頭不是i. 就加上去i.
                    img_url = img_url.split('//')[0]+'//i.'+img_url.split('//')[1]
                if img_url.endswith('.gif'):
                    pass
                elif img_url.endswith('.png'):
                    pass
                elif img_url.endswith('.jpg'):
                    pass
                else:  #如果尾巴沒有.jpg 加上個jpg檔名
                    img_url += '.jpg'
                fname = img_url.split('/')[-1] #切出最後段當作檔案名稱
                urllib.request.urlretrieve(img_url, os.path.join('All_picture',str(today),dname,fname))#放的資料路徑,os.path.join 106.6.3
                urllib.request.urlretrieve(img_url, os.path.join('Everyday_pictures',str(today),fname))#把資料另外存放一個總資料夾 106.6.3
        except Exception as e:
            print(e)
                
