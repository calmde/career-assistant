from scrapers.integrations import fetch_with_jobspy
res = fetch_with_jobspy(['python'], city='Beijing', max_pages=1)
print('Got', len(res), 'items')
if res:
    print(res[:3])
