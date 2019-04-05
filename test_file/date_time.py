# coding:utf-8
# Author:hxj
from datetime import datetime,date,timedelta


bd = '2019-04-04'
ed = '2019-04-05'

bd = datetime.strptime(bd,'%Y-%m-%d')
ed = datetime.strptime(ed,'%Y-%m-%d')


# bd = datetime.date(bd)
# ed = datetime.date(ed)

days = ed -bd + timedelta(1)


print bd
print ed
print days
print days.days
print type(days.days)






