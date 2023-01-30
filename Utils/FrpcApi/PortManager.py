class PortManager:
    PortList=[]
    def __init__(self,StartPort,EndPort):
        self.PortList.clear()
        for i in range(StartPort,EndPort):
            self.PortList.append(i)
        self.PortList.sort(reverse=True)
    def GetPort(self):
        if len(self.PortList)>0:
            return self.PortList.pop()
        else:
            return 0
    def AddPort(self,Port):
        self.PortList.append(Port)
        self.PortList.sort(reverse=True)
    def CheckPort(self):
        if len(self.PortList)>0:
            return True
        else:
            return False