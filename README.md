# CTFd-BerNet
基于kubernetes容器编排的ctfd平台动态题目靶场插件,支持Web题目以及pwn题部署.
## 环境说明
本插件是基于k8s v1.18.0版本开发,为保证兼容性等各种问题,请确保部署的主机上已经安装了Kubernetes集群(版本v1.18.0),相关组件如下:  
1.ingress-nginx  
2.确保default-http-backend正常  
简单来说就是集群环境已经能通过注册ingress快速部署业务上线.  
k8s集群可以全部部署在内网,也可以全部部署在外网.  

### 内网集群,外网vps
#### web题目环境
当集群全部部署在内网时,需要一个公网IP为内网集群提供一个接口,如果是使用云,则直接绑定LoadBalancer即可,如果使用vps映射,请将LoadBalancer的端口映射到vps公网上,确保web题目的动态域名能够通过ingress发布.
#### pwn题目环境
pwn类题目的流量不能通过ingress进行转发,所以需要直接使用端口映射,为此需要在集群内注册以下资源(请根据相关配置自行更改)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: frpc-config
data:
  frpc.ini: |
    [common]
    token=yourtoken
    server_addr = xxx.xxx.xxx.xxx
    server_port = xxxx
    admin_addr=0.0.0.0
    admin_port=7450
    admin_user = admin
    admin_pwd = yourpassword
---
apiVersion: v1
kind: Pod
metadata:
  name: ctfd-frpc
  labels:
    pod-name: ctfd-frpc
spec:
  containers:
  - name: ctfd-frpc
    image: m1t1/ctfd-bernet:frpc
    ports:
    - containerPort: 7450
      protocol: TCP
    volumeMounts:
    - name: ctfd-frpc-config
      mountPath: /var/frpc.ini
      subPath: frpc.ini
  volumes:
  - name: ctfd-frpc-config
    configMap:
      name: frpc-config
      items:
      - key: frpc.ini
        path: frpc.ini
---
apiVersion: v1
kind: Service
metadata:
  name: ctfd-frpc-service
spec:
  selector:
    pod-name: ctfd-frpc
  ports:
  - name: web
    port: 80
    targetPort: 7450
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: ctfd-frpc-ingress
spec:
  tls:
  - hosts:
    - xxx.com
    secretName: xxx-tls
  rules:
  - host: xxx.com
    http:
      paths:
      - path: /
        backend:
          serviceName: ctfd-frpc-service
          servicePort: 80
```
### 集群公网
对于集群在公网的情况,只需要确保frps和frpc的端口映射即可,主要保证pwn题的正常运行,对于web题目不需要多余的操作.
## 部署实践
### kubernetes集群部署
暂略.
### 插件部署
将项目下载后移至ctfd的CTFd/plugins目录下即可,目前测试支持到最新CTFd 3.5.1版本仍可用.
### 插件配置说明
#### k8s基础配置
确保k8s的基础配置正常,需要使用https,ca证书,token等验证.
![](https://cdn.zlimilz.cn/img/20230130200903.png)
#### 容器及web题目地址配置
配置提供了web题目地址使用https域名(提供相应的https证书即可),对于题目创建的容器则使用namespace对其进行隔离.
![](https://cdn.zlimilz.cn/img/20230130201036.png)
#### frpc配置
frpc配置简单易懂,对于pwn域名前缀为vps的IP地址,或者解析到vps的域名也可
![](https://cdn.zlimilz.cn/img/20230130201249.png)
## 案例
https://ctf.cdusec.com/
### Web题目
![](https://cdn.zlimilz.cn/img/20230130201411.png)
![](https://cdn.zlimilz.cn/img/20230130201454.png)
### Pwn题目
![](https://cdn.zlimilz.cn/img/20230130201521.png)
![](https://cdn.zlimilz.cn/img/20230130202214.png)
## 更新记录
2023-1-31 ~~修复了一个可能存在的安全隐患~~  
2023-2-2 ~~修复了一个bug~~,**新增了添加题目http的功能**  
2023-2-3 **新增了两个题目新的访问方式(HTTP:Port和IP:Port模式)**  
## 项目致谢&参考
感谢赵师傅和Frank师傅维护的ctfd-whale,本插件参考了很大部分ctfd-whale的代码.  
[ctfd-whale](https://github.com/glzjin/CTFd-Whale)  
[Frank师傅维护的ctfd-whale](https://github.com/frankli0324/ctfd-whale)  
