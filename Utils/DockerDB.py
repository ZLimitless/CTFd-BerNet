import datetime

from CTFd.models import db
from CTFd.utils import get_config
from ..WebDocker import BerNetContainer, RedirectTemplate


class DBContainer:
    @staticmethod
    def create_container_record(user_id, challenge_id): #创建容器记录
        container = BerNetContainer(user_id=user_id, challenge_id=challenge_id) # 记录开启容器的用户,和容器对应的题目ID
        db.session.add(container)
        db.session.commit()
        return container

    @staticmethod
    def get_current_containers(user_id): # 获取用户当前开启的容器
        q = db.session.query(BerNetContainer) # 查询容器
        q = q.filter(BerNetContainer.user_id == user_id) # 根据用户ID过滤容器
        return q.first() # 返回第一个值(开启的容器)

    @staticmethod
    def get_container_by_port(port): #
        q = db.session.query(BerNetContainer)
        q = q.filter(BerNetContainer.port == port) # 根据容器端口寻找题目
        return q.first() # 返回题目

    @staticmethod
    def remove_container_record(user_id):# 根据用户ID删除容器
        q = db.session.query(BerNetContainer) #
        q = q.filter(BerNetContainer.user_id == user_id)
        q.delete()
        db.session.commit()

    @staticmethod
    def get_all_expired_container():
        timeout = int(get_config("BerNet:MaxPodLivingTime", "3600")) #取设置容器过期时间
        q = db.session.query(BerNetContainer)
        q = q.filter(
            BerNetContainer.start_time <datetime.datetime.now() - datetime.timedelta(seconds=timeout)  #查询过期容器 nowtime-starttime>timeout
        )
        return q.all()  # 取出过期容器

    @staticmethod
    def get_all_alive_container():
        timeout = int(get_config("BerNet:MaxPodLivingTime", "3600"))

        q = db.session.query(BerNetContainer)
        q = q.filter(
            BerNetContainer.start_time >=
            datetime.datetime.now() - datetime.timedelta(seconds=timeout) # 查询存活容器 nowtime-starttime<=timeout
        )
        return q.all()

    @staticmethod
    def get_all_container():
        q = db.session.query(BerNetContainer) # 取出所有容器
        return q.all()

    @staticmethod
    def get_all_alive_container_page(page_start, page_end): # 根据页数显示存活容器
        timeout = int(get_config("BerNet:MaxPodLivingTime", "3600"))

        q = db.session.query(BerNetContainer)
        q = q.filter(
            BerNetContainer.start_time >=
            datetime.datetime.now() - datetime.timedelta(seconds=timeout)
        )
        q = q.slice(page_start, page_end)
        return q.all()

    @staticmethod
    def get_all_alive_container_count(): # 取出所有存活容器的数量
        timeout = int(get_config("BerNet:MaxPodLivingTime", "3600"))

        q = db.session.query(BerNetContainer)
        q = q.filter(
            BerNetContainer.start_time >=
            datetime.datetime.now() - datetime.timedelta(seconds=timeout)
        )
        return q.count()


class DBRedirectTemplate:
    @staticmethod
    def get_all_templates(): # 取所有渲染模板
        return RedirectTemplate.query.all()

    @staticmethod
    def create_template(name, access_template, frp_template): # 创建渲染模板
        if RedirectTemplate.query.filter_by(key=name).first(): # 判断是否已经在模板
            return  # already existed
        db.session.add(RedirectTemplate(
            name, access_template, frp_template
        ))
        db.session.commit()

    @staticmethod
    def delete_template(name): # 删除模板
        RedirectTemplate.query.filter_by(key=name).delete()
        db.session.commit()
