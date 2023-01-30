from flask import Blueprint

from CTFd.models import (
    db,
    Flags,
)
from CTFd.plugins.challenges import BaseChallenge
from CTFd.plugins.dynamic_challenges import DynamicValueChallenge
from CTFd.plugins.flags import get_flag_class
from CTFd.utils import user as current_user
from .WebDocker import BerNetContainer, DynamicDockerChallenge

from flask import Blueprint

from CTFd.models import (
    db,
    Flags,
)
from CTFd.plugins.challenges import BaseChallenge
from CTFd.plugins.dynamic_challenges import DynamicValueChallenge
from CTFd.plugins.flags import get_flag_class
from CTFd.utils import user as current_user
from .WebDocker import BerNetContainer, DynamicDockerChallenge

class DynamicValueDockerChallenge(BaseChallenge):
    id = "动态题目"  # Unique identifier used to register challenges
    name = "动态容器题目创建"  # Name of a challenge type
    blueprint = Blueprint(
        "ctfd-bernet-challenge",
        __name__,
        template_folder="templates",
        static_folder="assets",
    )
    challenge_model = DynamicDockerChallenge

    @classmethod
    def read(cls, challenge):
        challenge = DynamicDockerChallenge.query.filter_by(id=challenge.id).first()
        data = {
            "id": challenge.id, # 题目ID
            "name": challenge.name, # 题目名称
            "value": challenge.value,# 题目分数
            "initial": challenge.initial, #题目初始值
            "decay": challenge.decay, # 题目递减值
            "minimum": challenge.minimum, # 题目最小值
            "description": challenge.description, # 题目描述
            "category": challenge.category,# 题目分类
            "state": challenge.state, # 题目状态 可见/不可见
            "max_attempts": challenge.max_attempts,# 提交flag尝试次数
            "type": challenge.type,# 题目类型
            "type_data": {
                "id": cls.id,
                "name": cls.name,
                "templates": cls.templates,
                "scripts": cls.scripts,
            },
        }
        return data

    @classmethod
    def update(cls, challenge, request):
        data = request.form or request.get_json()

        for attr, value in data.items():
            if attr in ("initial", "minimum", "decay"):
                value = float(value)
            setattr(challenge, attr, value)

        if challenge.dynamic_score == 1:
            return DynamicValueChallenge.calculate_value(challenge)

        db.session.commit()
        return challenge

    @classmethod
    def attempt(cls, challenge, request):
        data = request.form or request.get_json()
        submission = data["submission"].strip()

        flags = Flags.query.filter_by(challenge_id=challenge.id).all()

        if len(flags) > 0:
            for flag in flags:
                if get_flag_class(flag.type).compare(flag, submission):
                    return True, "flag提交正确"
            return False, "flag提交错误"
        else:
            user_id = current_user.get_current_user().id # 取当前用户ID
            q = db.session.query(BerNetContainer) # 取当前容器
            q = q.filter(BerNetContainer.user_id == user_id) # 过滤当前容器
            q = q.filter(BerNetContainer.challenge_id == challenge.id)# 过滤当前题目ID
            records = q.all()# 记录
            if len(records) == 0:
                return False, "请在题目运行时提交flag"

            container = records[0]
            if container.flag == submission:
                return True, "提交正确"
            return False, "提交错误"

    @classmethod
    def solve(cls, user, team, challenge, request):
        super().solve(user, team, challenge, request)

        if challenge.dynamic_score == 1:
            DynamicValueChallenge.calculate_value(challenge)

        db.session.commit()

    @classmethod
    def delete(cls, challenge):
        for container in BerNetContainer.query.filter_by(
            challenge_id=challenge.id
        ).all():
            pass
        super().delete(challenge)