from configobj import ConfigObj

conf = ConfigObj('configs.conf')
for i in conf:
    print(conf[i])
