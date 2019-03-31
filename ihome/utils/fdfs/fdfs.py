# coding:utf-8
# Author:hxj
from fdfs_client.client import Fdfs_client


if __name__ == '__main__':
    client = Fdfs_client('client.conf')
    # ret = client.upload_by_filename(r'C:\Users\Administrator\Pictures\122123.png')
    f = open(r'C:\Users\Administrator\Pictures\122123.png','rb')
    ret = client.upload_by_buffer(f.read())
    f.close()

    print ret