import requests
from lxml import html
from flask_restful import Resource
import pandas as pd
from flask import request
import re
import threading
import numpy as np

main_news_csv = r"main_news.csv"


def fetch_main_news_data(category,news_page_url):
    
    news_df = pd.DataFrame(columns = ["category","headline","description","url","image_url"])

    last_page_xpath = "//div[contains(@class,'listng_pagntn clear')]/a[contains(@class,'btnLnk arrowBtn next')]/preceding-sibling::a[position()=1]"
    page = requests.get(news_page_url)
    tree = html.fromstring(page.content)
    total_pages = tree.xpath(last_page_xpath+"/text()")[0]
    
    headline_list = []
    description_list = []
    image_url_list = []
    url_list = []
    
    for page in range(1, int(total_pages) + 1):
        page_url = f"{news_page_url}/page-{page}"
        page = requests.get(page_url)
        tree = html.fromstring(page.content)
        news_header_xpath = "//h2[contains(@class,'newsHdng')]/a"
        
        headline_elements = tree.xpath(news_header_xpath)
        
        for i in range(1,int(len(headline_elements)) + 1):
            
            news_headline = tree.xpath(f"({news_header_xpath})[{i}]/text()")[0] #*headline
            news_url = headline_elements[i-1].get('href') #*url
            description_xpath = f"({news_header_xpath})[{i}]/parent::h2/following-sibling::p/text()"
            description = tree.xpath(description_xpath)[0] #*description
            img_xpath = f"({news_header_xpath})[{i}]/parent::h2/parent::div/preceding-sibling::div/a/img"
            img_url = tree.xpath(img_xpath)[0].get("src") #*image_url
            
            headline_list.append(news_headline)
            description_list.append(description)
            image_url_list.append(img_url)
            url_list.append(news_url)
            
    news_df["headline"] = headline_list
    news_df["description"] = description_list
    news_df["url"] = url_list
    news_df["image_url"] = image_url_list
    news_df = news_df.assign(category = category)
    
    return news_df


main_categories = {
    "latest" : "https://www.ndtv.com/latest",
    "india" : "https://www.ndtv.com/india",
    # "science" : "https://www.ndtv.com/science",
    # "business" : "https://www.ndtv.com/business/latest",
    # "entertainment" : "https://www.ndtv.com/entertainment/latest",
}
main_news_dataframe = pd.DataFrame(columns = ["category","headline","description","url","image_url"])

def store_news_in_csv():
    threading.Timer(120.0, store_news_in_csv).start()
    L = []
    for category in main_categories:
        df = fetch_main_news_data(category = category, news_page_url = main_categories[category])
        L.append(df)
    global main_news_dataframe
    main_news_dataframe = pd.concat(L, ignore_index=True)
    main_news_dataframe.to_csv(main_news_csv, sep = ',', index = False)



def read_dataframe(requested_fields = ["category","headline","description","url","image_url"],
                    requested_categories = ["latest","india"]):
    #total_main_news_df = main_news_dataframe.copy()
    total_main_news_df = pd.read_csv(main_news_csv)
    main_news_df_with_requested_fields = total_main_news_df[requested_fields]
    
    output_category_list = []
    for category in requested_categories:
        category_wise_df = main_news_df_with_requested_fields[main_news_df_with_requested_fields["category"]==category]
        category_wise_df = category_wise_df.replace({np.nan: None})
        
        news_list = []
        for index, row in category_wise_df.iterrows():
            response_dict = {i:row[i] for i in category_wise_df.columns}
            news_list.append(response_dict)
        
        category_dictionary = {
            "category" : category,
            "total_results" : len(category_wise_df),
            "news_list": news_list
        }
        
        output_category_list.append(category_dictionary)
    
    return {"status":"successfully fetched",
            "news":output_category_list}


#store_news_in_csv()

#read_dataframe()

class LatestNews(Resource):
    def get(self):
        user_requested_field = request.args.get("field")
        if user_requested_field is not None:
            fields_list = re.findall(r'([^(,)]+)(?!.*\()', user_requested_field)
            news_list = read_dataframe(requested_fields = fields_list)
        else:
            news_list = read_dataframe()
        return news_list

