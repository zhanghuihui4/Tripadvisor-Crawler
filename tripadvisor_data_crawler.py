import time
import math
import random

import pandas as pd
import numpy as np
from tqdm import tqdm
tqdm.pandas()

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains



class WebCrawler:
    def __init__(self,city,city_url,hotel_info_output_path,review_output_path):
        self.city = city
        self.city_url = city_url
        self.hotel_info_output_path = hotel_info_output_path
        self.review_output_path = review_output_path

    def setting_driver(self):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(options=options)
        return driver

    def open_url(self):
        driver = self.setting_driver()
        driver.get(self.city_url)
        driver.maximize_window()
        time.sleep(3)
        button = driver.find_element("xpath", '//div[@class="GWFhW f v u j"]')
        actions = ActionChains(driver)
        actions.move_to_element(button).perform()

        time.sleep(3)
        button.click()

        total_hotels = driver.find_element("xpath", '//div[@class="qWcyk f Q1"]').text
        num_hotels = int(total_hotels.split('propert')[0].replace(',', ''))
        return num_hotels

    def collect_info(self):
        driver = self.setting_driver()
        hotel_names = driver.find_elements("xpath", '//div[@class="nBrpc Wd o W"]')

        page_hotel_names = []
        for hotel_name in hotel_names:
            page_hotel_names.append(hotel_name.text)

        hotel_urls = driver.find_elements("xpath", '//a[@class="cCdhd Cg wSSLS"]')

        page_hotel_urls = []
        for hotel_url in hotel_urls:
            page_hotel_urls.append(hotel_url.get_attribute('href'))

        review_urls = driver.find_elements("xpath", '//div[@class="CJMXx o W f u w RBGDs"]')

        page_review_ratings = []
        page_review_vols = []
        for review_url in review_urls:
            txt = review_url.get_attribute('aria-label')
            page_review_ratings.append(txt.split('bubbles')[0].replace('of 5', '').strip())
            page_review_vols.append(
                txt.split('bubbles')[1].replace('.', '').replace('reviews', '').replace('review', '').replace(',',                                                                                                             '').strip())

        df = pd.DataFrame(list(zip(page_hotel_names, page_hotel_urls, page_review_ratings, page_review_vols)),
                          columns=['Name', 'Url', 'Rating', 'Review_vol'])
        return df

    def next_page(self):
        driver = self.setting_driver()
        driver.find_element("xpath", '//a[@aria-label="Next page"]').click()


    def get_hotel_urls(self):
        num_hotels = self.open_url()

        dfs = []
        df = self.collect_info()
        dfs.append(df)

        for i in tqdm(range(math.floor(num_hotels / 30))):
            self.next_page()
            time.sleep(3)
            df = self.collect_info()
            dfs.append(df)

        hotel_url_df = pd.concat(dfs)
        return hotel_url_df

    def get_hotel_info(self,url):
        driver = self.setting_driver()
        driver.get(url)
        driver.maximize_window()
        time.sleep(2)
        hotel_name = driver.find_element("xpath", '//h1[@class="biGQs _P rRtyp"]').text
        hotel_address = driver.find_element("xpath", '//span[@class="oAPmj _S "]').text

        try:
            hotel_ranking = driver.find_elements("xpath", '//a[@class="BMQDV _F Gv wSSLS SwZTJ FGwzt ukgoS"]')[1].text
        except:
            hotel_ranking = np.nan

        try:
            hotel_description = driver.find_element("xpath", '//div[contains(@class,"_T FKffI IGtbc Ci oYqEM")]').text
        except:
            hotel_description = np.nan

        try:
            hotel_class = driver.find_element("xpath", '//*[name()="svg" and @class="JXZuC d H0"]').get_attribute(
                'aria-label')
        except:
            hotel_class = np.nan

        try:
            style_urls = driver.find_elements("xpath", '//div[@class="euDRl _R MC S4 _a H"]')
            language = style_urls[-1].text
            hotel_styles = []
            for style_url in style_urls[:-1]:
                hotel_styles.append(style_url.text)
        except:
            language = np.nan
            hotel_styles = np.nan
        return hotel_name, hotel_address, hotel_ranking, hotel_description, hotel_class, language, hotel_styles

    def get_hotel_detailed_info(self):
        hotel_url_df = self.get_hotel_urls()

        hotel_url_df[['Hotel_name', 'Address', 'Ranking', 'Description', 'Class', 'Language',
            'Hotel_styles']] = hotel_url_df.progress_apply(lambda x: self.get_hotel_info(x['Url']),
                                                           axis=1, result_type='expand')

        hotel_url_df.to_csv(self.hotel_info_output_path + self.city + "_hotels.csv", index=False)
        return hotel_url_df

    def get_review_info(self):
        driver = self.setting_driver()
        reviews = driver.find_elements("xpath", '//div[@class="YibKl MC R2 Gi z Z BB pBbQr"]')

        page_review_info = []
        for review in reviews:
            try:
                reviewer = review.find_element("xpath", './/a[@class="ui_header_link uyyBf"]').get_attribute('href')
            except:
                reviewer = np.nan

            try:
                date = review.find_element("xpath", './/div[@class="cRVSd"]').text
            except:
                date = np.nan

            try:
                location = review.find_element("xpath", './/span[@class="RdTWF"]').text
            except:
                location = np.nan

            try:
                contribution = review.find_element("xpath", './/span[contains(text(),"contribution")]').text
            except:
                contribution = np.nan

            try:
                help_vote = review.find_element("xpath", './/span[contains(text(),"helpful vote")]').text
            except:
                help_vote = np.nan

            try:
                image_divs = review.find_elements("xpath", './/div[@class="MtByY _T PfFfr"]')
                if len(image_divs) > 0:
                    with_img = 't'
                else:
                    with_img = 'f'
            except:
                with_img = 'f'

            try:
                rating = review.find_element("xpath", './/span[contains(@class,"ui_bubble_rating")]').get_attribute(
                    'class').split()[1].replace('bubble_', '')
            except:
                rating = np.nan

            try:
                review_title = review.find_element("xpath", './/div[@class="KgQgP MC _S b S6 H5 _a"]').text
            except:
                review_title = np.nan

            try:
                review_content = review.find_element("xpath", './/span[@class="QewHA H4 _a"]').text
            except:
                review_content = np.nan

            try:
                date_of_stay = review.find_element("xpath", './/span[@class="teHYY _R Me S4 H3"]').text.replace(
                    'Date of stay:', '').strip()
            except:
                date_of_stay = np.nan

            try:
                response_title = review.find_element("xpath", './/div[@class="nNoCN n"]').text
            except:
                response_title = np.nan

            try:
                response_date = review.find_element("xpath", './/div[@class="miiHC"]').get_attribute('title')
            except:
                response_date = np.nan

            try:
                response_content = review.find_element("xpath", './/span[@class="MInAm _a"]').text
            except:
                response_content = np.nan

            try:
                response_helpful = review.find_element("xpath", './/span[@class="hVSKz S2 H2 Ch sJlxi"]').text.replace(
                    'Helpful vote', '').replace('s', '').strip()
            except:
                response_helpful = np.nan

            page_review_info.append(
                [reviewer, date, location, contribution, help_vote, with_img, rating, review_title, review_content,
                 date_of_stay, response_title, response_date, response_content, response_helpful])

        return page_review_info

    def review_next_page(self):
        driver = self.setting_driver()
        driver.find_element("xpath", '//a[@class="ui_button nav next primary "]').click()

    def crawl_reviews_by_hotel(self):
        hotel_url_df = self.get_hotel_detailed_info()

        hotel_url_df['Review_vol'] = hotel_url_df['Review_vol'].astype('int')


        all_hotels = hotel_url_df['Hotel_name'].tolist()
        all_urls = hotel_url_df['Url'].tolist()
        review_vols = hotel_url_df['Review_vol'].tolist()

        for i in range(len(hotel_url_df)):

            print("Crawling data for hotel: " + all_hotels[i])
            print("Now parsing data from: " + all_urls[i])
            print(str(review_vols[i]) + ' reviews in total!')

            driver = self.setting_driver()
            driver.get(all_urls[i])
            driver.maximize_window()
            time.sleep(2)

            try:
                driver.find_element("xpath", '//div[@data-test-target="expand-review"]').click()
            except:
                print('No read more button!')

            en_review_vol_labels = driver.find_elements("xpath", '//label[@class="Qukvo Vm _S"]')
            en_review_vols = [e.text for e in en_review_vol_labels]
            en_review_vols = [e for e in en_review_vols if e.find("English") != -1]
            en_review_vol = int(
                en_review_vols[0].replace('English', '').replace(',', '').replace('(', '').replace(')', '').strip())
            print(str(en_review_vol) + " English Reviews")

            hotel_review_info = []
            page_review_info = self.get_review_info()
            hotel_review_info += page_review_info

            for j in tqdm(range(math.floor(en_review_vol / 10))):
                try:
                    self.review_next_page()
                    sleep_time = random.randint(20, 40) / 10
                    time.sleep(sleep_time)
                    page_review_info = self.get_review_info()
                    hotel_review_info += page_review_info
                except Exception as error:
                    print('Failed loading page: ' + str(j))
                    print("An error occurred:", error)
                finally:
                    continue

            try:
                output_df = pd.DataFrame(hotel_review_info,
                                         columns=['reviewer', 'date', 'location', 'contribution', 'help_vote',
                                                  'with_img', 'rating', 'review_title', 'review_content',
                                                  'date_of_stay', 'response_title', 'response_date', 'response_content',
                                                  'response_helpful'])
                output_df['Hotel'] = all_hotels[i]
                output_df['Url'] = all_urls[i]
                output_df.to_csv(self.review_output_path + all_hotels[i].replace(' ', '_') + '.csv', index=False)
            except:
                print('Something went wrong when crawling data of ' + all_hotels[i])
            finally:
                continue


def main():
    city = 'Hong-Kong'
    city_url = 'https://www.tripadvisor.com/Hotels-g294217-Hong_Kong-Hotels.html'
    hotel_info_output_path = 'Hotels/Basic_info/'
    review_output_path = 'Hotels/online_reviews/'
    tripadvisor_crawler = WebCrawler(city,city_url,hotel_info_output_path,review_output_path)
    tripadvisor_crawler.crawl_reviews_by_hotel()


if __name__ == "__main__":
    main()