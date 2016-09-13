>>> from atomisator.parser import parse
>>> import os
>>> res = parse(os.path.join("tests", 'sample.xml'))
>>> res
<itertools.islice object at ...>
>>> res.next()
{'summary_detail': ...'links': [u'http://www.feedforall.com/restaurant.htm'], ...}
