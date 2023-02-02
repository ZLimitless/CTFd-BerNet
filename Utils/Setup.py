from CTFd.utils import set_config

def SetConfig():
    for key, val in {
        'Setup': 'true',
        'KubernetesUrl': "https://",#'https://url:6379',
        'KubernetesCA': "ca.crt",#'/etc/ca.crt',
        'KubernetesToken': "token",#'token',
        'MaxPodCount': '100',
        'MaxPodRenewCount': '5',
        'MaxPodLivingTime': '3600',
        'FrpApiUrl': 'http://admin:admin@127.0.0.1:7400',
        'PwnSubDomain':'pwn.ctf.cdusec.com',
        'SubDomain': 'ctf.cdusec.com',
        'HttpSubDomain':'httpctf.cdusec.com',
        'PwnMinPort': '32000',
        'PwnMaxPort': '32100',
        'SubNet':'10.10.10.0/24',
        'SubNetPrefix':'24',
        'TemplateHttpSubdomain': '{{ "ctf"+container.uuid|string }}',
        'TemplateFlag': '{{ "CduSec{"+uuid.uuid4()|string+"}" }}',
        'NameSpace':'XXX',
        'SecretName':'XXX',
        'UseHttps':'true',
        'SSLCACert':'path',
        'SSLCAKey':'path',
        'refresh':'true'
    }.items():
        set_config('BerNet:' + key, val)
        set_config('BerNet:FrpcTemplate','test')