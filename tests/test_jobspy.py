import traceback
try:
    import jobspy
    ver = getattr(jobspy, '__version__', 'unknown')
    print('JOBSPY_INSTALLED', ver)
    if hasattr(jobspy, 'search'):
        try:
            res = jobspy.search(keyword='python', city='北京', pages=1)
            print('SEARCH_RETURN_TYPE', type(res))
            try:
                print('LENGTH', len(res))
            except Exception:
                pass
            print('SAMPLE_ITEM', res[0] if hasattr(res, '__getitem__') and len(res)>0 else 'NO_ITEMS')
        except Exception as e:
            print('SEARCH_FAILED', e)
    else:
        print('JOBSPY_NO_SEARCH_FUNC', dir(jobspy)[:20])
except Exception as e:
    print('JOBSPY_NOT_AVAILABLE')
    traceback.print_exc()
