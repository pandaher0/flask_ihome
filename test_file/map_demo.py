# coding:utf-8
# Author:hxj


li1 = [1,2,3,4]
li2 = [2,3,4,5]
li3 = [3,4,5,6]

def add(num1,num2):
    return num1+num2

ret = map(add,li1,li2)
print ret

# python2 直接返回列表
# python3 返回map对象，需要转换成list