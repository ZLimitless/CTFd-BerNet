import datetime
import traceback

from CTFd.utils import get_config
from .DockerDB import DBContainer, db
from .K8sApi import KubernetesTools
from .FrpcApi import FRPCApi

class ControlUtil:
    K8sAPI=None
    FrpApi=None
    @staticmethod
    def init():
        try:
            ControlUtil.K8sAPI = KubernetesTools(APIUrl=get_config('BerNet:KubernetesUrl'), CA_Path=get_config('BerNet:KubernetesCA'),UserToken=get_config('BerNet:KubernetesToken'))
            ControlUtil.FrpApi=FRPCApi.FrpcApi(url=get_config('BerNet:FrpApiUrl'),PortMin=get_config('BerNet:PwnMinPort'),PortMax=get_config('BerNet:PwnMaxPort'))
        except:
            print("初始化失败")
    @staticmethod
    def try_add_container(user_id, challenge_id):
        container = DBContainer.create_container_record(user_id, challenge_id)
        flag=0
        containerUrl='NULL'
        containerIP='NULL'
        if container.challenge.redirect_type == 'http':
            try:
                flag,containerUrl=ControlUtil.K8sAPI.CreateContainerThreeInOne(NameSpace=get_config('BerNet:NameSpace'),PodName=container.uuid,ContainerPort=container.challenge.redirect_port,ENVFlag=container.flag,WebPort=80,ImageName=container.challenge.docker_image,SubDomainName=get_config('BerNet:SubDomain'),SecretName=get_config('BerNet:SecretName'),MemoryLimit=container.challenge.memory_limit,CPULimit=container.challenge.cpu_limit)
                print(containerUrl)
            except Exception as e:
                DBContainer.remove_container_record(user_id)
                print(traceback.format_exc())
                return False, '题目容器创建失败'
            if flag == 8 or ('创建失败' in containerUrl):
                DBContainer.remove_container_record(user_id)
                return False, '题目容器创建失败'
            if get_config('BerNet:SubDomain') not in containerUrl:
                ok = False
            else:
                ok = True
            if not ok:
                try:
                    ControlUtil.K8sAPI.DeleteContainerThreeInOne(NameSpace=get_config('BerNet:NameSpace'),PodName=container.uuid)
                except:
                    return False, f'题目创建并删除失败.'
                DBContainer.remove_container_record(user_id)
                return False, f'题目创建失败'
            container.url=container.uuid + '.' + get_config('BerNet:SubDomain')
            db.session.commit()
            return True, '题目环境创建成功'
        if container.challenge.redirect_type == 'direct':
            TempPort = ControlUtil.FrpApi.PortGet()
            container.port = TempPort
            container.url= 'nc ' + get_config('BerNet:PwnSubDomain') + " "+ str(container.port)
            db.session.commit()
            flag,containerIP=ControlUtil.K8sAPI.CreatePwnContainer(NameSpace=get_config('BerNet:NameSpace'),PodName=container.uuid,ContainerPort=container.challenge.redirect_port,EnvFlag=container.flag,VPSPort=TempPort,ImageName=container.challenge.docker_image,MemoryLimit=container.challenge.memory_limit,CPULimit=container.challenge.cpu_limit)
            print(containerIP)
            if flag==8:
                DBContainer.remove_container_record(user_id)
                ControlUtil.FrpApi.PortBack(TempPort)
                return False, '题目容器创建失败'
            if '.' in containerIP:
                if ControlUtil.FrpApi.PortAdd(PodName=container.uuid, IP=containerIP,Port=TempPort, RemotePort=TempPort):
                    print("端口映射成功")
                    return True, '题目环境创建成功'
                else:
                    try:
                        ControlUtil.K8sAPI.DeleteContainerThreeInOne(NameSpace=get_config('BerNet:NameSpace'),PodName=container.uuid)
                    except:
                        return False,f'题目记录创建失败,容器删除失败'
                    DBContainer.remove_container_record(user_id)
                    ControlUtil.FrpApi.PortBack(TempPort)
                    return False, f'题目创建失败'
            return True, '题目环境创建成功'

    @staticmethod
    def try_remove_container(user_id):
        container = DBContainer.get_current_containers(user_id=user_id)
        if not container:
            return False, '没有找到对应的题目容器'
        for _ in range(3):  
            try:
                ok=ControlUtil.K8sAPI.DeleteContainerThreeInOne(get_config('BerNet:NameSpace'),container.uuid)
                if not ok:return False
                if container.challenge.redirect_type== 'direct':
                    ok=ControlUtil.FrpApi.PortDelete(container.uuid)
                if not ok: return False
                DBContainer.remove_container_record(user_id)
                return True, '题目容器已经销毁'
            except Exception as e:
                print(traceback.format_exc())
        DBContainer.remove_container_record(user_id)
        return False, '删除容器失败,请联系管理员'

    @staticmethod
    def try_renew_container(user_id):
        container = DBContainer.get_current_containers(user_id)
        if not container:
            return False, '没有找到对应的题目容器'
        timeout = int(get_config("BerNet:MaxPodLivingTime", "3600"))
        container.start_time = container.start_time + datetime.timedelta(seconds=timeout)
        if container.start_time > datetime.datetime.now():
            container.start_time = datetime.datetime.now()
        else:
            return False, '无效的容器'
        container.renew_count += 1
        db.session.commit()
        return True, '容器重新计时成功'
