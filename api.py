import time
from datetime import datetime

from flask import request
from flask_restx import Namespace, Resource, abort

from CTFd.utils import get_config
from CTFd.utils import user as current_user
from CTFd.utils.decorators import admins_only, authed_only

from .Utils.decorators import challenge_visible, frequency_limited
from .Utils.CreateDB import ControlUtil
from .Utils.DockerDB import DBContainer
import requests

admin_namespace = Namespace("ctfd-bernet-admin")
user_namespace = Namespace("ctfd-bernet-user")


@admin_namespace.errorhandler
@user_namespace.errorhandler
def handle_default(err):
    return {
        'success': False,
        'message': 'Unexpected things happened'
    }, 500


@admin_namespace.route('/container')
class AdminContainers(Resource):
    @staticmethod
    @admins_only
    def get():
        page = abs(request.args.get("page", 1, type=int))
        results_per_page = abs(request.args.get("per_page", 20, type=int))
        page_start = results_per_page * (page - 1)
        page_end = results_per_page * (page - 1) + results_per_page
        count = DBContainer.get_all_alive_container_count()
        containers = DBContainer.get_all_alive_container_page(
            page_start, page_end)

        return {'success': True, 'data': {
            'containers': containers,
            'total': count,
            'pages': int(count / results_per_page) + (count % results_per_page > 0),
            'page_start': page_start,
        }}

    @staticmethod
    @admins_only
    def patch():
        user_id = request.args.get('user_id', -1)
        result, message = ControlUtil.try_renew_container(user_id=int(user_id))
        if not result:
            abort(403, message, success=False)
        return {'success': True, 'message': message}

    @staticmethod
    @admins_only
    def delete():
        user_id = request.args.get('user_id')
        result, message = ControlUtil.try_remove_container(user_id)
        try:
            DBContainer.remove_container_record(user_id)
        except:
            pass
        return {'success': result, 'message': message}


@user_namespace.route("/container")
class UserContainers(Resource):
    @staticmethod
    @authed_only
    @challenge_visible
    def get():
        user_id = current_user.get_current_user().id
        challenge_id = request.args.get('challenge_id')
        container = DBContainer.get_current_containers(user_id=user_id)
        if not container:
            print(user_id,challenge_id,container)
            return {'success': True, 'data': {}}
        timeout = int(get_config("BerNet:MaxPodLivingTime", "3600"))
        if int(container.challenge_id) != int(challenge_id):
            return abort(403, f'已经有一个非本题目的环境开启 ,题目名称为:{container.challenge.name}', success=False)
        if container.challenge.redirect_type== 'direct':
            return {
                'success': True,
                'data':{
                    'Command' :container.url,
                    'remaining_time': timeout - (datetime.now() - container.start_time).seconds,
                }
            }
        else:
            return {
                'success': True,
                'data': {
                    'lan_domain': container.url,
                    'remaining_time': timeout - (datetime.now() - container.start_time).seconds,
                }
            }

    @staticmethod
    @authed_only
    @challenge_visible
    @frequency_limited
    def post():
        user_id = current_user.get_current_user().id
        current_count = DBContainer.get_all_alive_container_count()
        if int(get_config("BerNet:MaxPodCount")) <= int(current_count):
            abort(403, '题目环境数量已达上限,请稍后重试', success=False)
        container = None
        container = DBContainer.get_current_containers(user_id=user_id)
        if container:
            return abort(403, f'已经有一个非本题目的环境开启 ,题目名称为:{container.challenge.name}', success=False)
        challenge_id = request.args.get('challenge_id')
        result, message = ControlUtil.try_add_container(
            user_id=user_id,
            challenge_id=challenge_id
        )
        if not result:
            abort(403, message, success=False)
        return {'success': True, 'message': message}

    @staticmethod
    @authed_only
    @challenge_visible
    @frequency_limited
    def patch():
        user_id = current_user.get_current_user().id
        challenge_id = request.args.get('challenge_id')
        docker_max_renew_count = int(get_config("BerNet:MaxPodRenewCount", 5))
        container = DBContainer.get_current_containers(user_id)
        if container is None:
            abort(403, 'Instance not found.', success=False)
        if int(container.challenge_id) != int(challenge_id):
            abort(403, f'已经有一个非本题目的环境开启（{container.challenge.name}）', success=False)
        if container.renew_count >= docker_max_renew_count:
            abort(403, '到达续时环境数量上线', success=False)
        result, message = ControlUtil.try_renew_container(user_id=user_id)
        return {'success': result, 'message': message}

    @staticmethod
    @authed_only
    @frequency_limited
    def delete():
        user_id = current_user.get_current_user().id
        result, message = ControlUtil.try_remove_container(user_id)
        if not result:
            abort(403, message, success=False)
        return {'success': True, 'message': message}
