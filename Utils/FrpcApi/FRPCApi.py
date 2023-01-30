import requests
from . import PortManager
from configparser import ConfigParser
class FrpcApi:
    sessions=requests.session()
    ConfigAllText=""
    PortManager=None
    Url=""
    def __init__(self,url,PortMin,PortMax):
        self.PortManager=PortManager.PortManager(PortMin,PortMax)
        print(self.PortManager.GetPort())
        if FrpcApi.CheckFrpc(url):
            self.Url=url
            self.ConfigAllText = self.sessions.get(url+'/api/config').text
    @staticmethod
    def CheckFrpc(url):
        try:
            FrpcConfig=requests.get(url+'/api/config',timeout=3)
            if 'common' in FrpcConfig.text:
                print("FrpcApi初始化成功")
                return True,FrpcConfig.text
            else:
                return False, "FrpcApi初始化失败"
        except:
            print("FrpcApi初始化失败")
            return False,"FrpcApi初始化失败"
    def ConfigGet(self):
        FrpcConfig = self.sessions.get(self.Url + '/api/config')
        if FrpcConfig.status_code==200:
            return FrpcConfig.text
        else:
            return "获取配置失败"
    class FrpRule:
        def __init__(self, name, config):
            self.name = name
            self.config = config
        def __str__(self) -> str:
            return f'[{self.name}]\n' + '\n'.join(f'{k} = {v}' for k, v in self.config.items())
    def PortAdd(self,PodName,IP,Port,RemotePort):
        Rules=[]
        config=self.ConfigGet()
        Config={
            'local_ip':IP,
            'local_port':Port,
            'remote_port':RemotePort,
            'use_compression': 'true',
        }
        Rules.append(self.FrpRule(PodName,Config))
        try:
            if str(Port) not in config:
                config = config + '\n' + '\n'.join(str(r) for r in Rules)
                if self.sessions.put(url=self.Url+'/api/config',data=config,timeout=5).status_code==200:
                    pass
                if self.sessions.get(url=self.Url+'/api/reload',timeout=2).status_code==200:
                    print("添加配置成功")
                    return True
            else:
                print("配置已经存在")
        except:
            print("添加配置失败!")
            return False
        print(self.ConfigGet())
    # def PortDelete(self,Podname):
    def PortDelete(self,PodName):
        Rules = []
        ConfigNew=""
        ConfigText=self.ConfigGet()
        config=ConfigParser()
        config.read_string(ConfigText)
        try:
            OldPort=config.get(PodName,"remote_port")
            config.remove_section(PodName) # 删除映射
            config_dict = {sect: dict(config.items(sect)) for sect in config.sections()}
        except:
            print("config配置出错")
        for i in config.sections():
            Rules.append(self.FrpRule(i, config_dict[i]))
        ConfigNew=ConfigNew+ '\n' + '\n'.join(str(r) for r in Rules) # 新的配置文件
        try:
            if self.sessions.put(url=self.Url+'/api/config',data=ConfigNew,timeout=5).status_code==200:
                pass
            if self.sessions.get(url=self.Url+'/api/reload',timeout=2).status_code==200:
                self.PortManager.AddPort(int(OldPort))
                print("删除映射成功")
                return True
        except:
            print("删除配置失败")
            return False
    def PortGet(self):return self.PortManager.GetPort()
    def PortBack(self,Port): self.PortManager.AddPort(Port)