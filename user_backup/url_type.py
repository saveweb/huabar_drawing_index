Q = 'qiniu'
A = 'ali'
W = 'wbm'
B = 'bad'

def get_urltype(url: str):
    # haowanlab 七牛杭州
    if url.startswith('http://qncdn.haowanlab.com/'):
        return Q
    elif url.startswith('http://haowanlab.qiniudn.com/'): # 标准形式
        return Q

    # haowanlab 阿里杭州
    elif url.startswith('http://haowanlab.oss-cn-hangzhou.aliyuncs.com/'): # 标准形式
        return A
    elif url.startswith('https://haowanlab.oss-cn-hangzhou.aliyuncs.com/'):
        return A
    elif url.startswith('http://oss-cn-hangzhou.aliyuncs.com/haowanlab/'):
        return A
    elif url.startswith('http://haowanlab.oss.aliyuncs.com/'):
        return A

    # 少数资源
    elif url.startswith('http://huaba-operate.oss-cn-hangzhou.aliyuncs.com/'):
        return W
    elif url.startswith('http://notecontent.oss-cn-hangzhou.aliyuncs.com/'):
        return W

    # BAD URLs
    elif url.startswith('http://imax.vmall.com/'):
        return B
    elif url == " ?x-oss-process=style/picmax":
        return B
    elif url == '"(null)"' or url == '(null)':
        return B

    else:
        raise ValueError('Unknown URL: ' + url)
