from . import FRPCApi
def create_frpc_api(username,password,url):
    FrpcApi=FRPCApi.FrpcApi(url)
    return FrpcApi
