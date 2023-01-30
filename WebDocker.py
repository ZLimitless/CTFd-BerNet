import random
import uuid
from datetime import datetime

from jinja2 import Template

from CTFd.utils import get_config
from CTFd.models import db, Challenges

class DynamicDockerChallenge(Challenges):
    __mapper_args__ = {"polymorphic_identity": "动态题目"}
    id = db.Column(None, db.ForeignKey("challenges.id",
                                       ondelete="CASCADE"), primary_key=True)
    initial = db.Column(db.Integer, default=0) #题目初始分数
    minimum = db.Column(db.Integer, default=0) #动态题目最低分数
    decay = db.Column(db.Integer, default=0) # 每次题目递减的分数
    memory_limit = db.Column(db.Integer, default="128") #题目内存限制
    cpu_limit = db.Column(db.Integer, default='500')# 题目CPU限制
    dynamic_score = db.Column(db.Integer, default=0) #

    docker_image = db.Column(db.Text, default=0) # 镜像名称
    redirect_type = db.Column(db.Text, default=0) # 题目模式 web题目为http模式 pwn题目为端口模式
    redirect_port = db.Column(db.Integer, default=0) # 容器端口

    def __init__(self, *args, **kwargs):
        super(DynamicDockerChallenge, self).__init__(**kwargs)
        self.initial = kwargs["value"]

class BerNetConfig(db.Model):
    key = db.Column(db.String(length=128), primary_key=True) # 键值对设置
    value = db.Column(db.Text)

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __repr__(self):
        return "<BerNetConfig {0} {1}>".format(self.key, self.value)

class RedirectTemplate(db.Model):
    key = db.Column(db.String(20), primary_key=True) # 键值对设置
    frp_template = db.Column(db.Text) # frp模板
    access_template = db.Column(db.Text) # 容器模板

    def __init__(self, key, access_template, frp_template):
        self.key = key
        self.access_template = access_template
        self.frp_template = frp_template

    def __repr__(self):
        return "<RedirectTemplate {0}>".format(self.key)


class BerNetContainer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # 容器ID
    user_id = db.Column(None, db.ForeignKey("users.id")) # 用户ID
    challenge_id = db.Column(None, db.ForeignKey("challenges.id")) #题目ID
    start_time = db.Column(db.DateTime, nullable=False,default=datetime.utcnow) #容器开启时间
    renew_count = db.Column(db.Integer, nullable=False, default=0) #容器重启的次数
    status = db.Column(db.Integer, default=1) # 容器状态
    uuid = db.Column(db.String(256))# 容器uuid
    port = db.Column(db.Integer, nullable=True, default=0) # 容器端口 pwn题使用
    flag = db.Column(db.String(128), nullable=False) # 容器flag
    url=db.Column(db.String(256)) # 容器题目地址
    # Relationships
    user = db.relationship(
        "Users", foreign_keys="BerNetContainer.user_id", lazy="select") # 开启容器的用户,与CTFd平台用户连接
    challenge = db.relationship(
        "DynamicDockerChallenge", foreign_keys="BerNetContainer.challenge_id", lazy="select" ) # 外键建立,同步ctfd题目类型

    @property
    def http_subdomain(self): # 容器域名访问方式
        return Template(get_config(
            'BerNet:TemplateHttpSubdomain', '{{ container.uuid }}' # 取设置,如果没有则默认UUID
        )).render(container=self)


    def __init__(self, user_id, challenge_id,Port=0):
        self.user_id = user_id # 用户ID
        self.challenge_id = challenge_id #题目ID
        self.start_time = datetime.now() # 容器开启时间
        self.renew_count = 0 # 容器重启次数
        self.uuid = str('ctf'+str(uuid.uuid4())[0:13]) # 题目URL路径
        # self.port=Port #Pwn题目映射的端口
        self.flag = Template(get_config(
            'BerNet:TemplateFlag', '{{ "flag{"+uuid.uuid4()|string+"}" }}' # 取设置,默认为flag{}格式
        )).render(container=self, uuid=uuid, random=random, get_config=get_config) # 初始化容器信息

    @property
    def user_access(self):  # 用户访问方式
        return Template(RedirectTemplate.query.filter_by(
            key=self.challenge.redirect_type # 容器访问方式 http,tcp
        ).first().access_template).render(container=self, get_config=get_config)


    def __repr__(self):
        return "<Container ID:{0} {1} {2} {3} {4}>".format(self.id, self.user_id, self.challenge_id,
                                                                self.start_time, self.renew_count)