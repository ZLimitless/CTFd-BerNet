import warnings

import requests
from flask import Blueprint, render_template, session, current_app, request
from flask_apscheduler import APScheduler

from CTFd.api import CTFd_API_v1
from CTFd.plugins import (
    register_plugin_assets_directory,
    register_admin_plugin_menu_bar,
)
from CTFd.plugins.challenges import CHALLENGE_CLASSES
from CTFd.utils import get_config, set_config
from CTFd.utils.decorators import admins_only
from .Utils.Setup import SetConfig
from .ChallengeType import DynamicValueDockerChallenge
from .api import user_namespace, admin_namespace, AdminContainers
from .Utils.K8sApi import KubernetesTools
from .Utils.CreateDB import ControlUtil
from .Utils.DockerDB import DBContainer
from .Utils.FrpcApi.FRPCApi import FrpcApi
def load(app):
    plugin_name = __name__.split('.')[-1]
    set_config("BerNet:plugin_name",plugin_name)
    print("plugin_name",get_config('BerNet:plugin_name'))
    app.db.create_all()
    SetConfig()
    # if not get_config("BerNet:setup"):
    #     SetConfig()
    register_plugin_assets_directory(
        app, base_path=f"/plugins/{plugin_name}/assets",
        endpoint='plugins.ctfd-bernet.assets'
    )
    register_admin_plugin_menu_bar(
        title='BerNet',
        route='/plugins/ctfd-bernet/admin/settings'
    )
    DynamicValueDockerChallenge.templates = {
        "create": f"/plugins/{plugin_name}/assets/create.html",
        "update": f"/plugins/{plugin_name}/assets/update.html",
        "view": f"/plugins/{plugin_name}/assets/view.html",
    }
    DynamicValueDockerChallenge.scripts = {
        "create": f"/plugins/{plugin_name}/assets/create.js",
        "update": f"/plugins/{plugin_name}/assets/update.js",
        "view": f"/plugins/{plugin_name}/assets/view.js",
    }
    CHALLENGE_CLASSES["动态题目"] = DynamicValueDockerChallenge
    page_blueprint = Blueprint(
        "ctfd-bernet",
        __name__,
        template_folder="templates",
        static_folder="assets",
        url_prefix="/plugins/ctfd-bernet"
    ) # 注册蓝图
    CTFd_API_v1.add_namespace(admin_namespace, path="/plugins/ctfd-bernet/admin") # 根据命名空间确定用户权限,注册api
    CTFd_API_v1.add_namespace(user_namespace, path="/plugins/ctfd-bernet")
    worker_config_commit = None
    @page_blueprint.route('/admin/settings')
    @admins_only
    def admin_list_configs():
        nonlocal worker_config_commit
        print(type(get_config('BerNet:refresh')),get_config('BerNet:refresh')) #or (not get_config('BerNet:refresh') and get_config('BerNet:UseHttps') or (not get_config('BerNet:refresh') and get_config("BerNet:NameSpace") != '')
        if get_config('BerNet:refresh') :
            errors=[]
            CheckFlag,CheckMessage=KubernetesTools.CheckToken(APIUrl=get_config('BerNet:KubernetesUrl'),CA_Path=get_config('BerNet:KubernetesCA'),UserToken=get_config('BerNet:KubernetesToken'))
            errors.append(CheckMessage)
            FrpcFlag,FrpcConfig=FrpcApi.CheckFrpc(get_config('BerNet:FrpApiUrl'))
            if CheckFlag and FrpcFlag:
                ControlUtil.init()
                api = KubernetesTools(APIUrl=get_config('BerNet:KubernetesUrl'),CA_Path=get_config('BerNet:KubernetesCA'),UserToken=get_config('BerNet:KubernetesToken'))
                if get_config("BerNet:NameSpace") != '':
                    flag, Err = api.CreateNameSpace(get_config("BerNet:NameSpace"))
                    if flag:errors.append(Err),set_config('BerNet:refresh','false')
                    #else:CheckFlag=False
                if get_config('BerNet:UseHttps'):
                    print("Secret create....")
                    flag, Err = api.CreateSecret(NameSpace=get_config('BerNet:NameSpace'),CrtPath=get_config('BerNet:SSLCACert'),KeyPath=get_config('BerNet:SSLCAKey'),SecretName=get_config('BerNet:SecretName'))
                    if flag:errors.append(Err),set_config('BerNet:refresh','false')
                    else:errors.append(Err)
            if FrpcFlag:
                set_config('BerNet:FrpcTemplate',FrpcConfig)
                errors.append("FrpcAPI配置成功")
            else:
                errors.append("FrpcAPI配置失败")
            return render_template('bernet-config.html', errors=errors)
        # if CheckFlag and get_config("BerNet:refresh") != worker_config_commit:
        #     worker_config_commit = get_config("BerNet:refresh")
        #     #KubernetesTools.init()
        #     #Router.reset()
        #     set_config("BerNet:refresh", "false")
        return render_template('bernet-config.html',errors=[f'配置正常']) #, errors=errors
    @page_blueprint.route("/admin/containers")
    @admins_only
    def admin_list_containers():
        result = AdminContainers.get()
        print(result)
        view_mode = request.args.get('mode', session.get('view_mode', 'list'))
        session['view_mode'] = view_mode
        print(view_mode)
        return render_template('bernet-containers.html',
                               plugin_name=plugin_name,
                               containers=result['data']['containers'],
                               pages=result['data']['pages'],
                               curr_page=abs(request.args.get("page", 1, type=int)),
                               curr_page_start=result['data']['page_start'])

    app.register_blueprint(page_blueprint)
    def auto_clean_container():
        with app.app_context():
            results = DBContainer.get_all_expired_container()
            for r in results:
                ControlUtil.try_remove_container(r.user_id)
    try:
        scheduler = APScheduler()
        scheduler.init_app(app)
        scheduler.start()
        scheduler.add_job(
            id='auto-clean', func=auto_clean_container,
            trigger="interval", seconds=10
        )
        print("CTFD-BerNet启动成功,定时任务创建成功")
    except:
        pass
    @app.route('/admin/login.php')
    def test():
        return "hacker?hello?"