#coding:utf-8
'''成员'''
from ..lib.request import WechatRequest

class Person(object):
    def __init__(self):
        self.__requests = WechatRequest() 
        self.data = None
    
    #获取部门列表
    def get_department_list(self):
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/list"
        self.data = self.__requests.get(url)
        return self.data

    #获取成员
    def get_part(self,userid):
        #userid:成员UserID。对应管理端的帐号,必须键
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/get"
        
        params={"userid":userid}
        self.data = self.__requests.get(url,params)
        return self.data
    #获取部门成员
    def get_part_person(self,department_id,fetch_child=0,status=0):
        """
        department_id 	是 	获取的部门id
        fetch_child 	否 	1/0：是否递归获取子部门下面的成员
        status 	否 	0获取全部成员，1获取已关注成员列表，2获取禁用成员列表，4获取未关注成员列表。status可叠加，未填写则默认为4         
        """
        
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/simplelist"
        params={"department_id":department_id,"fetch_child":fetch_child,"status":status}
        self.data = self.__requests.get(url,params)
        return self.data["userlist"]
    #获取部门成员(详情)
    def get_part_person_verbose(self,department_id,fetch_child=0,status=1):

        url = "https://qyapi.weixin.qq.com/cgi-bin/user/list"
        params={"department_id":department_id,"fetch_child":fetch_child,"status":status}
        self.data = self.__requests.get(url,params)
        return self.data["userlist"]

    #添加成员
    def add_part_person(self,params):
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/create"
        self.data = self.__requests.post(url,params)
        return  self.data

    #编辑部门成员信息
    def edit_part_person(self,params):
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/update"
        self.data = self.__requests.post(url,params)
        return self.data

    #删除部门成员
    def del_part_person(self,params):
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/delete"
        self.data = self.__requests.get(url,params)
        return self.data

    
    