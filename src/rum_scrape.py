"""
NAME
    rum_scrape

DESCRIPTION
    A simple web scraper for the site RumRatings.

CONTENTS
    ScrapeRums() - main function that collects data and saves out to a dataframe
    BayesianRum() - calculates a bayesian score for each rum
"""

import bs4
import requests
import pandas as pd
import time


def ScrapeRums(page_start=1, page_end=288, df_name='data/rum_data.csv', sleep_time=10):
    """ The main function that collects data from the rumrankings site, as scraping can take a while you
        can grab a page at a time. Currently 7/18/2020 288 is the last page. The price column is a premium
        feature on the site so that will be completely sparse. Additionally the site also combines the name
        of the rum with the brand with no distinction so it is difficult to determine what the brand is. To
        do this I compare the combined name with a list or previously known brands (the file rum_companies.txt),
        if found that name is used, otherwise it is currently being labeled 'Unknown'.

    Args:
        page_start : which page to start on, the initial page should be 1
        page_end : which page to stop on, this number is inclusive
        df_name : file name to load / save values from
        sleep_time : how many seconds to sleep between requests

    Return:
        None
    """
    file_company = open('data/rum_companies.txt')
    company_names = [line.strip() for line in file_company]

    for page in range(page_start, page_end+1):
        names, country, types, ratings, price, score, img_url, rum_url, company = [], [], [], [], [], [], [], [], []
        hdr = {'User-Agent': 'Mozilla/5.0'}
        url = f'https://www.rumratings.com/brands?order_by=name&page={page}'
        req = requests.get(url, headers=hdr)
        print(url)

        if req.status_code == 200:
            soup = bs4.BeautifulSoup(req.text, 'html.parser')
            results = soup.find_all('div', class_='rum-title')

            # name, country, type, price, and # of ratings are all jammed in the same tag
            for r in results:
                text = r.text.strip(' \n').split('\n')
                names.append(text[0].strip(' '))
                text = text[-1].split(' | ')

                country.append(text[0])
                types.append(text[1])
                ratings.append(text[2].split(' ')[0])
                text = text[3].replace('$', '') if len(text) > 3 else '0.0'
                text = text.replace(',', '')
                price.append(text)

            results = soup.find_all('div', class_='rum-rating-icon')
            for r in results:
                score.append(r.text.strip(' \n'))

            results = soup.find_all('img')
            # quite hacky, but there are quite a lot of other images on the page, each image is also dupcliated
            for r in results[13:61:2]:
                img_url.append(r['data-src'])

            results = soup.find_all('a', class_='thumbnail')
            for r in results:
                rum_url.append(r['href'])

            # not thrilled about this part, check the rum's name to see if it matches a known company, if not set to 'unkown'
            for name in names:
                for c_name in company_names:
                    if name.startswith(c_name):
                        company.append(c_name)
                        break
                else:
                    company.append('Unknown')

            # create a new df from page results and append to what we already have, or create a brand new one
            try:
                df = pd.read_csv(df_name)
            except:
                df = pd.DataFrame(columns=['name', 'country', 'type', 'ratings', 'price', 'score', 'img_url', 'rum_url', 'company'])

            to_add = pd.DataFrame({'name':names, 'country':country, 'type':types, 'ratings':ratings, 'price':price, 'score':score, 'img_url':img_url, 'rum_url':rum_url, 'company':company})
            df = df.append(to_add, ignore_index=True, sort=True)
            df.to_csv(df_name, index=False)
            
            time.sleep(sleep_time)
        else:
            print('Connection Error!')

def BayesianRum(in_file='data/rum_data.csv', out_file=None):
    """ As the original data set does not have any bayesian rating it can be difficult to figure out the
        popularity of any given rum, once all rum information has been collected we can calculate our own.

    Args:
        in_file: the file name of the data set to load
        out_file: where to save the modified data set, None to overwrite original

    Return:
        None
    """

    try:
        df = pd.read_csv(in_file)
        avg_votes, avg_rating = df['ratings'].mean(), df['score'].mean()
        df['br_score'] = ((avg_votes * avg_rating) + (df['ratings'] * df['score'])) / (avg_votes + df['ratings'])
        df.to_csv(out_file if out_file != None else in_file, index=False)
    except:
        print(f'{in_file} not found!')

if __name__ == '__main__':
    print('Scrape Responsibly')
