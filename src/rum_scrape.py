import bs4
import requests
import pandas as pd
import time

def ScrapeRums():
    PAGE_START = 151 # starts at 1, ends at 288 as of 7/16/2020
    PAGE_END = 288
    file_company = open('rum_companies.txt')
    company_names = [line.strip() for line in file_company]

    for page in range(PAGE_START, PAGE_END+1):
        names, country, types, ratings, price, score, img_url, rum_url, company = [], [], [], [], [], [], [], [], []
        hdr = {'User-Agent': 'Mozilla/5.0'}
        url = f'https://www.rumratings.com/brands?order_by=name&page={page}'
        req = requests.get(url, headers=hdr)
        print(url)

        if req.status_code == 200:
            soup = bs4.BeautifulSoup(req.text, 'html.parser')
            results = soup.find_all('div', class_='rum-title')
            for thing in results:
                text = thing.text.strip(' \n').split('\n')
                names.append(text[0].strip(' '))
                text = text[-1].split(' | ')

                country.append(text[0])
                types.append(text[1])
                ratings.append(text[2].split(' ')[0])
                text = text[3].replace('$', '') if len(text) > 3 else '0.0'
                text = text.replace(',', '')
                price.append(text)

            results = soup.find_all('div', class_='rum-rating-icon')
            for thing in results:
                score.append(thing.text.strip(' \n'))

            results = soup.find_all('img')
            for thing in results[13:61:2]:
                text = thing['data-src']
                img_url.append(text)

            results = soup.find_all('a', class_='thumbnail')
            for thing in results:
                rum_url.append(thing['href'])

            for name in names:
                for c_name in company_names:
                    if name.startswith(c_name):
                        company.append(c_name)
                        break
                else:
                    company.append('Unknown')

            df = pd.read_csv('rum_data.csv')
            to_add = pd.DataFrame({'name':names, 'country':country, 'type':types, 'ratings':ratings, 'price':price, 'score':score,
                            'img_url':img_url, 'rum_url':rum_url, 'company':company})
            df = df.append(to_add, ignore_index=True, sort=True)
            df.to_csv('rum_data.csv', index=False)
            
            time.sleep(10)

def BayesianRum():
    df = pd.read_csv('rum_data.csv')
    avg_votes, avg_rating = df['ratings'].mean(), df['score'].mean()
    df['br_score'] = ((avg_votes * avg_rating) + (df['ratings'] * df['score'])) / (avg_votes + df['ratings'])
    df.to_csv('rum_data.csv', index=False)

# ScrapeRums()
BayesianRum()
