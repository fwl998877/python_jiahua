#coding:utf-8

from ..wechatLib.application.person import Person
from ..models import OrderForm
from ..wechatLib.application.send import Send
from django.db.models import Count
from ..wechatLib.config import DOMAIN
import logging
import time

class Driver(Person):
    def __init__(self):
        self.person = Person()
        self.send = Send()
        
    #得到东风乘用车司机车牌和userid
    def get_cat(self,createTime= time.strftime("%Y-%m-%d")):#{车牌号:[用户id号列表],是否已指派,[用户姓名]}
        result = self.person.get_part_person_verbose(3)
        dics = {}
        if isinstance(createTime,list):
            orderQuerySet = OrderForm.objects.filter(createTime__range = (createTime[0],createTime[1]))   
        else:
            orderQuerySet = OrderForm.objects.filter(createTime = createTime)   
        for value in result:
            userid = value["userid"]
            name = value["name"]#姓名
            
            if not value.get("extattr"):#防止没有设置车牌号
                continue
            for v in value["extattr"]["attrs"]:
                if u"车牌" == v["name"]:
                    cat =  v["value"]
            

            if dics.has_key(cat):
                dics[cat][0].append(userid)
                dics[cat][2].append(name)
            else:
                result = orderQuerySet.filter(plateNum__contains=cat).exists()
                dics[cat] = [[userid],result,[name]]
        return dics    
    #获取车牌号对应的用户id
    def get_userId_by_plateNum(self,plateNum,tranFormat=False,name=False):
        catDict=self.get_cat()
        user=catDict.get(plateNum)
        if not user:
            return []
        userList = user[0]#用户id列表
        
        #修改为微信格式
        if tranFormat:
            newUserList = ""
            for i in userList:
                newUserList = newUserList + i + "|"
            userList = newUserList.encode("utf-8")
            
        if name:#如果需要名字
            return [userList,user[2]]
        else:
            return userList
        
    #获取姓名通过用户id
    def get_name_by_userid(self,userId):
        catDict=self.get_cat()
        for plateNum,userList in catDict.iteritems():
            useridList = userList[0]
            nameList = userList[2]
            for i in range(len(useridList)):
                if userId == useridList[i]:
                    return nameList[i]
                
    #获取车牌号通过姓名
    def get_plateNum_by_name(self,name):
        catDict=self.get_cat()
        for plateNum,userList in catDict.iteritems():
            useridList = userList[0]
            nameList = userList[2]
            for i in range(len(nameList)):
                if name == nameList[i]:
                    return plateNum
            
    #获取用户id的车牌号
    def get_plateNum_by_userId(self,userId):
        catDict=self.get_cat()
        for plateNum,userList in catDict.iteritems():
            userList = userList[0]
            if userId in userList:
                return plateNum
            
    #获取司机信息
    def get_driver(self):
        result = self.person.get_part_person_verbose(3)
        lists = []
        for value in result:        
            mobile = value.get("mobile","")#电话
            name = value.get("name","")#名字
            tup = value.get("avatar","")#图像
            #email = value["email"]#邮件
            weixinid = value.get("weixinid","")   
            if value.get("extattr"):#防止没有车牌号
                for v in value["extattr"]["attrs"]:
                    if u"车牌" == v["name"]:
                        cat =  v["value"]
            else:
                cat = ""
            lists.append([name,weixinid,mobile,cat,tup])
        return lists            
    #获取车牌号对应的订单
    def get_orderId_by_plateNum(self,plateNum,createTime=time.strftime("%Y-%m-%d")):
        orderList = []
        idList=OrderForm.objects.filter(createTime=createTime,plateNum=plateNum).values_list("id")
        for i in idList:
            orderList.append(i[0])
        return orderList
            
            
            
    #通过id给司机发送消息
    def post_message_by_id(self,userid,data):
        self.send.sendText(content=data, agentid=1,touser=userid)
    #通过车牌号给司机发送消息
    def post_message_by_plateNum(self,plateNum,data):
        userList=self.get_userId_by_plateNum(plateNum,tranFormat=True)
        self.send.sendText(content=data, agentid=1,touser=userList)
    
    #指派订单
    def post_order(self,orderIdList,plateNum,operator=""):
        orderQuerySet = OrderForm.objects.filter(id__in=orderIdList)
        oldPlateNum = orderQuerySet[0].plateNum#旧车
        createTime = time.strftime("%Y-%m-%d")
        for item in orderQuerySet:
            #获得时间
            createTime = item.createTime
            #初始化数据
            item.receiveFormTime = None
            item.receiveFormPerson = ""
            item.receiveGoodsTime = None
            item.receiveGoodsPerson = ""
            item.acceptTime = None
            item.acceptPerson = ""            
            #指派
            item.plateNum = plateNum
            item.stateType = 1
            item.operator = operator#操作员
            item.save()
        
        self.post_catNum(plateNum,createTime)#给司机发消息
        if oldPlateNum:#通知旧车辆
            self.post_message_by_plateNum(oldPlateNum, "%s,您的订单已取消"%oldPlateNum)
            self.post_catNum(oldPlateNum,createTime)
            
    
    #给司机发送一车的消息[[orderid,orderid]..[orderid,orderid]]
    def post_catNum(self,plateNum,createTime=time.strftime("%Y-%m-%d")):
        logging.info("给司机发送%s的消息"%createTime)
        userList,nameList=self.get_userId_by_plateNum(plateNum,name=True)#获取车牌号对应的用户id
        orderQuerySet = OrderForm.objects.filter(createTime=createTime,plateNum=plateNum).order_by("catNum","tranNum","placeNum")
        #orderQuerySet = OrderForm.objects.filter(id__in=orderIdList).order_by("catNum","tranNum","placeNum")
        
        
        url=DOMAIN+"/wechat/order/today/?orderList="
        tranNum = -1#第几趟
        finish = 1#是否完成订单
        data = []
        tranObject = {}#趟数对象
        for item in orderQuerySet:
            if item.tranNum != tranNum:#如果是一个新的趟
                if tranObject:
                    
                    tranStr = ""
                    for i in tranObject["idList"]:
                        tranStr += str(i)
                        tranStr += "_"
                        
                    tranObject["url"] = url + tranStr
                
                    if finish ==1:#如果该趟全部完成
                        tranObject["finish"] = 1
                    else:
                        tranObject["finish"] = 0
                    finish =1#重置
                    if item.stateType!=4:
                        finish = 0
                    data.append(tranObject)
                    
                tranNum = item.tranNum
                if item.stateType!=4:
                    finish=0
                tranObject = {"tranNum":tranNum,"plateCount":1,"idList":[item.id]}   
                
                
            elif item.tranNum == tranNum:#如果是当前趟
                tranObject["plateCount"] += 1#任务总数加1
                tranObject["idList"].append(item.id)#添加id
                if item.stateType != 4 :#如果订单没有签收
                    finish = 0
                    
        #循环结束添加最后一趟
        if tranObject:
            tranStr = ""
            for i in tranObject["idList"]:
                tranStr += str(i)
                tranStr += "_"            
            
            tranObject["url"] = url + tranStr
            if finish == 1:
                tranObject["finish"] = 1
            else:
                tranObject["finish"] = 0
            data.append(tranObject)
        
        for useri in range(len(userList)):
            userid = userList[useri].encode("utf-8")
            name = nameList[useri].encode("utf-8")
            
            #数据处理部分
            content = []
            for one in data:
                tranOne = {}
                tranOne["title"] = "第%s趟"%one["tranNum"]
                description = "该趟有%s个任务"%one["plateCount"]
                tranOne["title"] = tranOne["title"]+" "+ "("+description +")"
                if one["finish"] == 1:
                    tranOne["title"] += " (已完成)"                
                tranOne["url"] = one["url"] + "&name=%s"%name
                content.append(tranOne)
                
            #做一个新闻头部
            tranOne = {}
            tranOne["title"] = "%s"%createTime    +" "+ "共有%s趟"%len(content)
            #tranOne["description"] = "%s,%s"%(plateNum,name)
            content.insert(0,tranOne)

            self.send.sendNews(contentList=content, agentid=1,touser=userid)
            
    #给司机发送历史订单
    def post_history(self,userid):
        name = self.get_name_by_userid(userid).encode("utf-8")
        
        #计算最近半年时间
        historyTime = [[time.localtime().tm_year,time.localtime().tm_mon]]
        for i in range(5):
            lastTime = historyTime[-1]
            if lastTime[1] == 1:
                currentTime = [lastTime[0]-1,12]
            else:
                currentTime = [lastTime[0],lastTime[1]-1]
            historyTime.append(currentTime)
        
        content = []
        for currentTime in historyTime:
            orderQuerySet = OrderForm.objects.filter(receiveFormTime__year=currentTime[0],receiveFormTime__month=currentTime[1],receiveFormPerson=name)
            receiveCount = orderQuerySet.count()#接单量
            acceptCount = orderQuerySet.filter(acceptPerson = name).count()#签单量
            
            tranOne = {}
            tranOne["title"] = "%s年%s月,接%s单,完成%s单"%(currentTime[0],currentTime[1],receiveCount,acceptCount)
            tranOne["url"] = DOMAIN + "/wechat/order/history/?name=%s&year=%s&mon=%s"%(name,currentTime[0],currentTime[1])
            content.append(tranOne)
        
        self.send.sendNews(contentList=content, agentid=1,touser=userid.encode("utf-8"))

            
            
            

        
        
        


