from scrapers.integrations import fetch_v2ex_jobs, fetch_dianya_jobs, fetch_xhiring_jobs

keywords = ['python']
for kw in keywords:
    print('=== Keyword:', kw)
    v2 = fetch_v2ex_jobs(kw)
    print('V2EX returned', len(v2))
    if v2:
        print('Sample:', v2[:3])
    dy = fetch_dianya_jobs(kw)
    print('Dianya returned', len(dy))
    if dy:
        print('Sample:', dy[:3])
    xh = fetch_xhiring_jobs(kw)
    print('X-Hiring returned', len(xh))
    if xh:
        print('Sample:', xh[:3])
