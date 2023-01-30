import base64

import yaml
from time import sleep
from kubernetes import client,config
class KubernetesTools:
    APPApi=None
    CoreApi=None
    CoreV1Api=None
    NetworkingV1Api=None
    def __init__(self,APIUrl,CA_Path, UserToken):
        configuration = client.Configuration()
        configuration.host = APIUrl  # api-server地址
        configuration.ssl_ca_cert = r"{}".format(CA_Path)
        configuration.verify_ssl = True
        configuration.api_key = {"authorization": "Bearer " + UserToken}  # 指定Token字符串
        client.Configuration.set_default(configuration)
        self.APPApi=client.AppsV1Api()
        self.CoreApi=client.CoreApi()
        self.CoreV1Api=client.CoreV1Api()
        self.NetworkingV1Api=client.NetworkingV1beta1Api()
    @staticmethod
    def CheckToken(APIUrl,CA_Path, UserToken):
        try:
            configuration = client.Configuration()
            configuration.host = APIUrl  # api-server地址
            configuration.ssl_ca_cert = r"{}".format(CA_Path)
            configuration.verify_ssl = True
            configuration.api_key = {"authorization": "Bearer " + UserToken}  # 指定Token字符串
            client.Configuration.set_default(configuration)
            version = client.CoreApi().get_api_versions()
            print("版本:" + str(version.versions))
            return True,f'kubernetes连接成功,CoreApi版本:{str(version.versions)}'
        except Exception as e:
            print(e)
            print(APIUrl,CA_Path)
            return False,f'kubernetes连接失败.'
    def GetPods(self,NameSpace):
        ret = self.CoreV1Api.list_namespaced_pod(namespace=NameSpace)
        return ret
    def CreatePod(self,NameSpace,PodName,ContainerPort,ENVFlag,ImageName,MemoryLimit,CPULimit,Re=False):
        body=client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(name=PodName,labels={"pod-name":PodName}),
            spec=client.V1PodSpec(
                containers=[client.V1Container(
                    name=PodName,
                    image=ImageName,
                    env=[client.V1EnvVar(name="FLAG",value=ENVFlag),client.V1EnvVar(name="FLAG-FAKE",value="this-is-fake-flag")],
                    ports=[client.V1ContainerPort(container_port=ContainerPort)],
                    resources=client.V1ResourceRequirements(
                        limits={'memory':str(int(MemoryLimit))+"Mi",'cpu':str(CPULimit)+"m"},
                        requests={'memory':str(int(MemoryLimit)-int(int(MemoryLimit)/3))+"Mi",'cpu':str(int(CPULimit)-int(int(CPULimit)/3))+"m"}
                    )
                    )],
                image_pull_secrets=[client.V1LocalObjectReference(
                    name="ctf-docker"
                )],
                )
            )
        print(body)
        try:
            PodIP=self.CoreV1Api.create_namespaced_pod(namespace=NameSpace,body=body).status.pod_ip
        except Exception as e:
            status = getattr(e, "status")
            if status == 400:
                print(e)
                return print("格式错误")
            elif status == 403:
                return print("没有权限")
        return PodName

    def DeletePod(self,NameSpace,PodName): # 成功返回true
        try:
            self.CoreV1Api.delete_namespaced_pod(namespace=NameSpace,name=PodName)
        except Exception as e:
            status = getattr(e, "status")
            reason = getattr(e, "reason")
            print("reason=",reason)
            if "Not Found" in reason:
                print("目标pod不存在")
                return True
            elif status == 403:
                print("没有权限")
            elif status != 200:
                print(e)
                print("删除失败")

        sleep(0.5)
        return True
    def GetService(self,NameSpace):
        ret=self.CoreV1Api.list_namespaced_service(namespace=NameSpace)
        return ret
        return
    def CreateService(self,NameSpace,ServiceName,PodName,Port,TargetPort,Re=False):
        Service=None
        body=client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(
                name=ServiceName,
            ),
            spec=client.V1ServiceSpec(
                selector={"pod-name":PodName},
                ports=[client.V1ServicePort(
                    port=Port, # Service的端口
                    target_port=TargetPort # Container端口
                )]
            )
        )
        try:
            Service=self.CoreV1Api.create_namespaced_service(NameSpace,body=body)
        except Exception as e:
            status = getattr(e, "status")
            if status == 400:
                print(e)
                return print("格式错误")
            elif status == 403:
                return print("没有权限")
        if Re:
            return True,Service.spec.cluster_ip
        return True
    def CreatePwnContainer(self,NameSpace,PodName,ContainerPort,VPSPort,EnvFlag,ImageName,MemoryLimit,CPULimit):
        print("开始创建pwn题目")
        flag=0
        i=0
        IP=''
        while flag!=2:
            i+=1
            if flag<1:
                if self.CreatePod(NameSpace=NameSpace,PodName=PodName,ContainerPort=ContainerPort,ENVFlag=EnvFlag,ImageName=ImageName,MemoryLimit=MemoryLimit,CPULimit=CPULimit) != PodName:
                    flag=0
                elif self.CheckPod(NameSpace,PodName):flag=1
                if 1<=flag<2:
                    Check,IP=self.CreateService(NameSpace=NameSpace,ServiceName=PodName,PodName=PodName,Port=VPSPort,TargetPort=ContainerPort,Re=True)
                    if not Check:
                        flag=1
                    elif self.CheckService(NameSpace,PodName):flag=2
            if i ==8:return i,f'创建失败'
        if flag==2:
            return True,IP
    def DeleteService(self,NameSpace,ServiceName): # 成功返回true
        try:
            self.CoreV1Api.delete_namespaced_service(namespace=NameSpace,name=ServiceName)
        except Exception as e:
            status = getattr(e, "status")
            reason = getattr(e, "reason")
            if "Not Found" in reason:
                print(e)
                print("Service删除失败原因:目标service不存在")
                return True
            elif status == 403:
                print("没有权限")
                return False
            elif status != 200 :
                print("Service删除失败")
                return False
        sleep(0.5)
        return True
    def GetIngress(self,NameSpace):
        ret=self.NetworkingV1Api.list_namespaced_ingress(namespace=NameSpace)
        return ret
    def CreateIngress(self,NameSpace,IngressName,ServiceName,PodName,ServicePort,SubDomainName,SecretName):
        IngressURL=PodName+"."+SubDomainName
        body=client.ExtensionsV1beta1Ingress(
            api_version="networking.k8s.io/v1beta1",#"extensions/v1beta1",
            kind="Ingress",
            metadata=client.V1ObjectMeta(
                name=IngressName
            ),
            spec=client.ExtensionsV1beta1IngressSpec(
                tls=[client.ExtensionsV1beta1IngressTLS(
                    hosts=[PodName+"."+SubDomainName],
                    secret_name=SecretName
                )],
                rules=[client.ExtensionsV1beta1IngressRule(
                    host=PodName+"."+SubDomainName,
                    http=client.ExtensionsV1beta1HTTPIngressRuleValue(
                        paths=[client.ExtensionsV1beta1HTTPIngressPath(
                            path="/",
                            backend=client.ExtensionsV1beta1IngressBackend(
                                service_name=ServiceName,
                                service_port=ServicePort
                            )
                        )]
                    )
                )]
            )
        )
        try:
            self.NetworkingV1Api.create_namespaced_ingress(namespace=NameSpace,body=body)
        except Exception as e:
            status = getattr(e, "status")
            if status == 400:
                print(e)
                return False
            elif status == 403:
                return False
        return IngressURL
    def DeleteIngress(self,NameSpace,IngressName): # 成功返回true
        try:
            self.NetworkingV1Api.delete_namespaced_ingress(namespace=NameSpace,name=IngressName)
        except Exception as e:
            status = getattr(e, "status")
            reason=getattr(e,"reason")
            if "Not Found" in reason:
                print("目标ingress不存在")
                return True
            elif status == 403:
                print("没有权限")
                return False
            elif status == 400:
                print(e)
                print("格式错误")
                return False
        return True
    def CreateContainerThreeInOne(self,NameSpace,PodName,ContainerPort,WebPort,ENVFlag,ImageName,SubDomainName,SecretName,MemoryLimit,CPULimit):
        print("开始创建ingress")
        ContainerURl=""
        flag=0
        i=0
        while flag!=3:
            i+=1
            if flag<1:
                if self.CreatePod(NameSpace=NameSpace, PodName=PodName, ContainerPort=ContainerPort, ENVFlag=ENVFlag,ImageName=ImageName,MemoryLimit=MemoryLimit,CPULimit=CPULimit) != PodName:
                    flag = 0
                elif self.CheckPod(NameSpace,PodName):flag=1
            if 1 <= flag < 2:
                test=self.CreateService(NameSpace=NameSpace, ServiceName=PodName, PodName=PodName, Port=WebPort,TargetPort=ContainerPort)
                if not test:
                    flag=1
                elif self.CheckService(NameSpace,PodName):flag=2
            if 2<=flag<3:
                ContainerURl = self.CreateIngress(NameSpace=NameSpace, IngressName=PodName, ServiceName=PodName,PodName=PodName, ServicePort=WebPort,SubDomainName=SubDomainName,SecretName=SecretName)
                if SubDomainName not in ContainerURl:flag=2
                elif self.CheckIngress(NameSpace,PodName):flag=3
            if i==8:
                return i,f'创建失败'
        if flag==3:
            return flag,ContainerURl
    def DeleteContainerThreeInOne(self,NameSpace,PodName):
        if not self.DeletePod(NameSpace,PodName):
            return False
        if not self.DeleteService(NameSpace,ServiceName=PodName):
            return False
        if not self.DeleteIngress(NameSpace,IngressName=PodName):
            return False
        return True
    def ListAll(self,NameSpace):
        PodList=[]
        for PodName in self.GetPods(NameSpace).items:
            PodList.append(PodName.metadata.name)
        ServiceList=[]
        for ServiceName in self.GetService(NameSpace).items:
            ServiceList.append(ServiceName.metadata.name)
        IngressList=[]
        for IngressName in self.GetIngress(NameSpace).items:
            IngressList.append(IngressName.metadata.name)
        # print("Pods:")
        # print(PodList)
        # print("Service:")
        # print(ServiceList)
        # print("Ingress:")
        # print(IngressList)
    def CheckContainer(self,NameSpace,ContainerName):
        if not self.CheckPod(NameSpace,ContainerName):
            print("pod创建失败")
            return False
        elif not self.CheckService(NameSpace,ContainerName):
            print("Service创建失败")
            return False
        elif not self.CheckIngress(NameSpace,ContainerName):
            print("Ingress创建失败")
            return False
        print("创建成功")
        return True
    def CheckPod(self,NameSpace,ContainerName):
        PodList=[]
        for PodName in self.GetPods(NameSpace).items:
            PodList.append(PodName.metadata.name)
        if ContainerName not in PodList:
            return False
        return True
    def CheckService(self,NameSpace,ContainerName):
        ServiceList=[]
        for ServiceName in self.GetService(NameSpace).items:
            ServiceList.append(ServiceName.metadata.name)
        if ContainerName not in ServiceList:
            return False
        return True
    def CheckIngress(self,NameSpace,ContainerName):
        IngressList=[]
        for IngressName in self.GetIngress(NameSpace).items:
            IngressList.append(IngressName.metadata.name)
        if ContainerName not in IngressList:
            return False
        return True
    def CreateNameSpace(self,NameSpace):
        flag = False
        IsConfig=0
        errors=f'test'
        body=client.V1Namespace(
            api_version='v1',
            kind='Namespace',
            metadata=client.V1ObjectMeta(name=NameSpace, labels={'name': NameSpace})
        )
        while not flag:
            if NameSpace not in self.GetName(self.CoreV1Api.list_namespace().items):
                print(self.GetName(self.CoreV1Api.list_namespace().items))
                flag=False
                IsConfig=0
            else:
                flag=True
                IsConfig+=1
                if IsConfig==1:errors=f'NameSpace已经存在'
                else:errors=f'NameSpace创建成功'
                return flag,errors
            if not flag:
                IsConfig=1
                self.CoreV1Api.create_namespace(body=body)
    def CreateSecret(self,NameSpace,CrtPath,KeyPath,SecretName):
        flag=False
        IsConfig=0
        errors=f"test"
        while not flag:
            print(self.GetName(self.CoreV1Api.list_namespaced_secret(NameSpace).items))
            if SecretName not in self.GetName(self.CoreV1Api.list_namespaced_secret(NameSpace).items):
                print(self.GetName(self.CoreV1Api.list_namespaced_secret(NameSpace).items))
                flag=False
            else:
                flag=True
                IsConfig+=1
                if IsConfig==1:errors=f'Secret Tls已存在'
                else:errors=f'Secret Tls不存在,但已经创建成功'
                return flag,errors
            if not flag:
                IsConfig+=1
                try:
                    CertBase64Data = base64.b64encode(open(CrtPath, 'rb').read())
                    KeyBase64Data = base64.b64encode(open(KeyPath, 'rb').read())
                    body = {
                        'apiVersion': 'v1',
                        'kind': 'Secret',
                        'metadata': {
                            'name': SecretName,
                            'namespace': NameSpace
                        },
                        'type': 'kubernetes.io/tls',
                        'data': {
                            'tls.crt': CertBase64Data,
                            'tls.key': KeyBase64Data
                        }
                    }
                    self.CoreV1Api.create_namespaced_secret(namespace=NameSpace,body=body)
                except:
                    if IsConfig==4:
                        break
        return False, f'Secret Tls创建失败,请检查配置'
    def GetName(self,Metadata):
        NameList=[]
        for i in Metadata:
            NameList.append(i.metadata.name)
        return NameList
    def RestartContainer(self,NameSpace,PodName,ContainerPort,ENVFlag,ImageName):
        try:
            if not self.DeletePod(NameSpace,PodName):
                return False,f'重启失败'
            if not self.CreatePod(NameSpace,PodName,ContainerPort,ENVFlag,ImageName):
                return False,f'重启失败'
            return True,f'重启成功'
        except:
            return False,f'重启失败'
