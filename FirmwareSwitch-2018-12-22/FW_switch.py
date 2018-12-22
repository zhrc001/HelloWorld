import sys
import os
import time
#import win32gui,win32api,win32con
import subprocess
import re
from time import strftime
import configparser
import platform
import traceback

name = str(strftime('%Y_%m_%d_%H%M')) + str('Switch.log')

SW_START_TIME = None


def api_assert(Value,BreakAftError):
    if BreakAftError == 1: 
        assert(Value)


def api_writefile(data):
    print(data)
    with open(name, 'a') as apendfile:
        apendfile.write(strftime('%Y-%m-%d-%H:%M:%S: ')+ data + "\n")

def check_no_service(Timeout = 60):
    #Waiting to complete the prompt,stop timer
    #Because the the update process windows does not have a available caption, so when can't use the windows to determine whether success
    #Instead that, if show mbn interface and the responde is OK, that it is success
    t1 = time.time()
    api_writefile("[info]: wait registering to the network")
    while 1:   #Wait to register to the network
        #res = api_check_ready()
        runCmd = "netsh m s i"
        p = subprocess.Popen(runCmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        while 1:
            x = p.poll()
            if x != None:
                break
            t = time.time() - t1
            if t > Timeout:
                if out != None:
                    api_writefile(out)
                api_writefile("[Error]: Home provider is not found, registration status is abnormal")
                return 1
            '''命令运行超时判断'''
        out=p.stdout.read()
        err=p.stderr.read()
        out = out.decode('gbk')
        #regex=re.compile("CHN-UNICOM")
        regex = re.compile("Provider Name\s*:\s*(CHN\S*)")
        HomeProvider = regex.findall(str(out))
        if len(HomeProvider) != 0:
            api_writefile(runCmd)
            api_writefile(out)
            api_writefile('[Success]: Home provider %s is found,registration is success'%(HomeProvider[0]))
            return 0




def api_Check_MBN_AT_CMD(AtCmd, Respond, TimeOut=5):
    time.sleep(1) # delay 1 second after the last AT finished.
    runCmd = "MbnAtTestApp.exe " + AtCmd
    api_writefile(runCmd)
    t1 = time.time()
    p = subprocess.Popen(runCmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    while 1:
        x = p.poll()
        if x != None:
            break
        t = time.time() - t1
        if t > TimeOut:
            api_writefile("[info]: Send %s %d time out " % (AtCmd,TimeOut))
            return 1
        '''命令运行超时判断'''
    out=p.stdout.read()
    err=p.stderr.read()
    out = out.decode('gbk')
    api_writefile(out)
    if err != b"":
        api_writefile('[info]: "MbnAtTestApp.exe %s" Command error, error is %s ' % (AtCmd, str(err)))
        return 3
    regex=re.compile(Respond)
    if len(regex.findall(str(out))) == 0:
        api_writefile("[info]: Mismatch")
        return 3
    else:
        api_writefile('[Success]: The respond is correct')
        return 0

    

def api1_copy_switch_table(sourceDir):
    sourceFile = os.path.join(sourceDir, "switchtable.xml")
    #targetFile = "C:\\Program Files (x86)\\Intel_XMM7360\\fwswitchbin\\config\\switchtable.xml"
    targetFile = api1_get_section_value('Setting.ini', "path", "SwitchTablePath")

    try:
        if os.path.exists(sourceFile):
            open(targetFile, "wb").write(open(sourceFile, "rb").read())
            return 0
        else:
            api_writefile("[Error]: Can't find switchtable.xml in %s" % sourceDir)
    except:
        api_writefile("[Error]: Copy file error")



#######################################################
# parameter:
# string: 1=S3 2=S4 3=restart Service
def api1_trigger_switch(string):
    #ret = os.system('tasklist | find "FirmwareApp.exe"')
    api_writefile("[info]: Trigger switching process")
    if getattr(sys, 'frozen', False):
        path = os.path.dirname(sys.executable)
    elif __file__:
        path = os.path.dirname(__file__)

    #S3
    if string == 1:
        api_writefile("[info]: Enter S3")
        hibernate = path + "\\Tool//pwrtest.exe /sleep /c:1 /d:30 /p:30" 
        process = subprocess.Popen(hibernate, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (output, err) = process.communicate()

    #S4
    if string == 2:
        api_writefile("[info]: Enter S4")
        hibernate = path + "\\Tool//pwrtest.exe /sleep /c:1 /s:4 /d:30 /p:30"
        process = subprocess.Popen(hibernate, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        (output, err) = process.communicate()

    #restart service
    if string == 3:
        api_writefile("[info]: Restart FirmwareSwitchService")
        runCmd = 'sc stop "FirmwareSwitchService"'
        p = subprocess.Popen(runCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while 1:
            x = p.poll()
            if x != None:
                break
        time.sleep(3)
        runCmd = 'sc start "FirmwareSwitchService"'
        p = subprocess.Popen(runCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while 1:
            x = p.poll()
            if x != None:
                break
    # disable -> restart service -> enable
    if string == 4:
        api_writefile("[info]: disable&enable MBIM")

        api_assert(api1_disable_MBIM()==0,1)
        runCmd = 'sc stop "FibocomSwitchService"'
        p = subprocess.Popen(runCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while 1:
            x = p.poll()
            if x != None:
                break
        runCmd = 'sc start "FibocomSwitchService"'
        p = subprocess.Popen(runCmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while 1:
            x = p.poll()
            if x != None:
                break
            
        api_assert(api1_enable_MBIM()==0,1)
    return 0


def api1_check_complete(ErrorTime = 120, WarnTime = 60):
    #Waiting to complete the prompt,stop timer
    #Because the the update process windows does not have a available caption, so when can't use the windows to determine whether success
    #Instead that, if show mbn interface and the responde is OK, that it is success
    global SW_START_TIME
    failLevel = 0
    time1 = time.time()

    api_writefile("[info]:Waiting for mobile broadband to get ready")
    while 1:   #Wait to register to the network
        #res = api_check_ready()
        runCmd = "netsh m s i"
        t1 = time.time()
        p = subprocess.Popen(runCmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
        while 1:
            x = p.poll()
            if x != None:
                break
            t = time.time() - t1
            if t > ErrorTime:
                #api_writefile("[info]: Send %s %d time out " % (AtCmd,TimeOut))
                return 1
            '''命令运行超时判断'''
        out=p.stdout.read()
        err=p.stderr.read()
        out = out.decode('gbk')
        #regex=re.compile("CHN-UNICOM")
        regex=re.compile("GSM")

        if len(regex.findall(str(out))) != 0:
            api_writefile(runCmd)
            api_writefile(out)
            #api_writefile('[Success]: "CHINA-UNICOM is found",Registration success')
            api_writefile('[Success]: mbn interface OK')
            break

        swEndTime = time.time()
        OutDuration = swEndTime - SW_START_TIME
        if OutDuration > WarnTime and failLevel == 0:
            api_writefile(runCmd)
            api_writefile(out)
            api_writefile("[Warning]: Switching time is over than %d seconds" % (WarnTime))
            failLevel = 1
        if swEndTime - SW_START_TIME > ErrorTime:
            api_writefile(runCmd)
            api_writefile(out)
            api_writefile("[Error]: Switching time is over than %d seconds" % (ErrorTime))
            failLevel = 2
            return(failLevel,OutDuration)
        time.sleep(1)
        
        
    while 1:  # check MBIM-AT is ready or not
        res = api_Check_MBN_AT_CMD("AT","OK",3)
        swEndTime = time.time()
        OutDuration = swEndTime - SW_START_TIME
        
        if res == 0:
            break
        if OutDuration > WarnTime and failLevel == 0:
            api_writefile("[Warning]: Switching time is over than %d seconds" % (WarnTime))
            failLevel = 1
        if OutDuration > ErrorTime:
            api_writefile("[Error]: Switching time is over than %d seconds" % (ErrorTime))
            failLevel = 2
            return(failLevel,OutDuration)
        time.sleep(1)
        
    return(failLevel,OutDuration)

# if registered to the network,that is ready
def api_check_ready():
    runCmd = "netsh m s i"
    api_writefile(runCmd)
    t1 = time.time()
    p = subprocess.Popen(runCmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    while 1:
        x = p.poll()
        if x != None:
            break
        t = time.time() - t1
        if t > 5:
            #api_writefile("[info]: Send %s %d time out " % (AtCmd,TimeOut))
            return 1
        '''命令运行超时判断'''
    out=p.stdout.read()
    err=p.stderr.read()
    out = out.decode('gbk')
    api_writefile(out)
    if err != b"":
        api_writefile('[info]: Command error, error is %s ' % (AtCmd, str(err)))
        return 3
    regex=re.compile("CHN-UNICOM")
    if len(regex.findall(str(out))) == 0:
        api_writefile("[info]: Mismatch")
        return 3
    else:
        api_writefile('[Success]: "CHINA-UNICOM is found",Registration success')
        return 0



def api1_check_MBN_AT_retry(AT,Respone,Timeout=30):
    time1 = time.time()
    while 1:
        res = api_Check_MBN_AT_CMD(AT,Respone)
        if res == 0:
            api_writefile("[success]: %s is correct" % (AT))
            return 0
        time2 = time.time()
        if time2 - time1 > Timeout:
            api_writefile("[Error]: Has retried %d seconds to check %s, but failed, '%s' is not found"% (Timeout,AT,Respone))
            return 1

def api1_get_section_value(SettingFileName,Section,ParameterName):
    #try:
        conf = configparser.ConfigParser()
        conf.read(SettingFileName)
        value = conf.get(Section, ParameterName)
        return value
    #except:
        api_writefile("[Info]:Reading setting file error: Section=%s, ParameterName=%s" % (Section, ParameterName))
        return None

def api1_disable_MBIM(WaitTime=10):
    if getattr(sys, 'frozen', False):
        pwd = os.path.dirname(sys.executable)
    elif __file__:
        pwd = os.path.dirname(__file__)
        
    osbit = platform.machine()

    if osbit == "AMD64":
        path = pwd + r"\Tool\devcon-ex\amd64"
    else:
        path = pwd + r"\Tool\devcon-ex\x86"
    os.chdir(path)
    
    t1 = time.time()
    timeout = 10
    p = subprocess.Popen("disable.bat", stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    while 1:
        x = p.poll()
        if x != None:
            break
        time.sleep(0.5)

        '''命令运行超时判断'''
        t2 = time.time()
        t = t2 - t1
        if t >= timeout:
            api_writefile('[Error]: Disable.bat %d seconds timeout' % timeout)
            return 1
    os.chdir(pwd)
    
    out=p.stdout.read()
    err=p.stderr.read()
    api_writefile(out.decode('gbk'))
    
    if err != b"":
        api_writefile("[Error]: Query service command run fail, error is: " + str(err))
        return 1
    regex=re.compile('boot')
    if len(regex.findall(str(out))) == 0: # doesn't match
        regex2=re.compile('1 device')
        if len(regex2.findall(str(out))) == 0:
            api_writefile("[Error]: Device is not found")
            return 2  # doesn't match
        else:
            api_writefile("[Success]: Disable MBIM")
            return 0  # match 1 device
    else:
        api_writefile("[Error]: Boot is found")
        return 2  # match   


def api1_enable_MBIM(WaitTimeAftEnabled=10):
    if getattr(sys, 'frozen', False):
        pwd = os.path.dirname(sys.executable)
    elif __file__:
        pwd = os.path.dirname(__file__)
        
    osbit = platform.machine()
    
    if osbit == "AMD64":
        path = pwd + r"\Tool\devcon-ex\amd64"
    else:
        path = pwd + r"\Tool\devcon-ex\x86"
    os.chdir(path)
    
    #os.system("enable.bat")

    t1 = time.time()
    timeout = 10
    p = subprocess.Popen("enable.bat", stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    while 1:
        x = p.poll()
        if x != None:
            break
        time.sleep(0.5)

        '''命令运行超时判断'''
        t2 = time.time()
        t = t2 - t1
        if t >= timeout:
            api_writefile('[Error]: Enable.bat %d seconds timeout' % timeout)
            return 1
    os.chdir(pwd)
    out=p.stdout.read()
    err=p.stderr.read()
    api_writefile(out.decode('gbk'))

    
    if err != b"":
        api_writefile("[Error]: Query service command run fail, error is: " + str(err))
        return 1
    regex=re.compile('boot')
    if len(regex.findall(str(out))) == 0: # doesn't match
        regex2=re.compile('1 device')
        if len(regex2.findall(str(out))) == 0:
            api_writefile("[Error]: '1 device' is found")
            return 2  # doesn't match
        else:
            api_writefile("[Success]: Enabled MBIM")
            return 0  # match 1 device
    else:
        api_writefile("[Error]: Boot is found")
        return 2  # match

def api_ping_test(host,timeout):
    try:
        t1 = time.time()
        while 1:
            p = subprocess.Popen("ping -l 1 -n 1 "+ host,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            while 1:
                x = p.poll()
                if x != None:
                    break

                '''ping命令运行超时判断'''
                time.sleep(1)
                t2 = time.time()
                t = t2 - t1
                if t >= timeout:
                    api_writefile('Ping ' + str(host) + " time out: " + str(timeout) + ' seconds')
                    api_writefile(out.decode('gbk'))
                    return 0
                
            out=p.stdout.read()
            err=p.stderr.read()
 
            if err != b"":
                api_writefile("Ping failed, error is: ",err)
                return 0

            t = t2 - t1
            regex=re.compile('TTL')
            if len(regex.findall(str(out))) == 0:
                pass
            else:
                return t
    except Exception as e:
        api_writefile("api_ping_test(): %s" % str(e))

def api1_ping_test(host,timeout):
    if timeout > 0:
        netStatus = api_ping_test(host,timeout) 

        if netStatus == 0:
            api_writefile("[Warning]: ping " + host + " " + str(timeout) + "s was failed")
            netStatus = api_ping_test("www.baidu.com",timeout)  

            if netStatus == 0:
                api_writefile("[Warning]: ping " + host + " " + str(timeout) + "s was failed again")
                netStatus = api_ping_test("www.hao123.com",timeout)

                if netStatus == 0:
                    api_writefile("[Error]: ping www.hao123.com" + " " + str(timeout) + "s was failed again")
                    counter = int(api_get_section_value("Setting.conf", "ErrorCounter", "cnt_ping_error"))
                    api_set_section_value("Setting.conf",
                                          "ErrorCounter",
                                          "cnt_ping_error",
                                          str(counter+1)
                                          )
                    return 0
        api_writefile("[Success]: Ping " + host + " is success, spend " + str(netStatus) + " seconds")
        return netStatus
    else:
        return 1


def tsc_firmware_switch(Total = 1000,
                        sourceDir = None
                        ):

    global SW_START_TIME
    SWDuration1 = []
    SWDuration2 = []
    SWDuration3 = []
    SWDuration4 = []
    SWDuration5 = []
    
    successCount = 0
    failCount = 0
    warnCount = 0
    totalSucess = 0.0
    totalWarning = 0.0

    Firmware1 = api1_get_section_value('Setting.ini', "Firmware", "Firmware1")
    Firmware2 = api1_get_section_value('Setting.ini', "Firmware", "Firmware2")
    CarrierID1 = api1_get_section_value('Setting.ini', "CarrierID", "CarrierID1")
    CarrierID2 = api1_get_section_value('Setting.ini', "CarrierID", "CarrierID2")
    Trigger = int(api1_get_section_value('Setting.ini', "Trigger", "Trigger"))
    CheckRegistration = int(api1_get_section_value('Setting.ini', "CheckOption", "CheckRegistration"))
    TimeofPingCheck = int(api1_get_section_value('Setting.ini', "CheckOption", "TimeofPingCheck"))
    LoopToCheckAT = int(api1_get_section_value('Setting.ini', "CheckOption", "LoopToCheckAT"))

    Breakafterr = int(api1_get_section_value('Setting.ini', "Breakafterr", "Breakafterr"))
    
    assert(Firmware1 != None) 
    assert(Firmware2 != None) 
    
    for i in range(1,Total + 1):
        if TimeofPingCheck != 0:
            api_assert(api1_ping_test("www.baidu.com",TimeofPingCheck),Breakafterr)

        api_writefile("*"*20 + "Loop Cycle: %d" % i )

        if i%2 == 1: #Replace the switchtable.xml with the file in folder1 when the test number is odd
            api_writefile("[info]: Copy switchTable1 to config fodler")
            api1_copy_switch_table(".\switchTable1")
        else:
            api_writefile("[info]: Copy switchTable2 to config fodler")
            api1_copy_switch_table(".\switchTable2")

        api_assert(api1_trigger_switch(Trigger)==0,Breakafterr)
        SW_START_TIME = time.time()
        time.sleep(15)
        #res = api1_wait_trigger_and_click(60,7)
        #if res != 0:
        #    api_writefile("[Error]: Switch is not trigged")
        #    return
        
        resGroup = api1_check_complete()
        api_assert(resGroup[0] != 2, Breakafterr)

        api_writefile("[info]: check carrier ID")
        if i%2 == 1:
            #api_assert(api_Check_MBN_AT_CMD("AT+GTCURCAR?",CarrierID1,30)==0, Breakafterr)
            #api_assert(api_Check_MBN_AT_CMD("ATI8", Firmware1 ,30)==0,Breakafterr)
            api_assert(api1_check_MBN_AT_retry("AT+GTCURCAR?",CarrierID1, LoopToCheckAT)==0,Breakafterr)
            api_assert(api1_check_MBN_AT_retry("ATI8", Firmware1, LoopToCheckAT)==0,Breakafterr)
        else:
            api_assert(api1_check_MBN_AT_retry("AT+GTCURCAR?",CarrierID2, LoopToCheckAT)==0, Breakafterr)
            api_assert(api1_check_MBN_AT_retry("ATI8", Firmware2, LoopToCheckAT)==0, Breakafterr)

        if CheckRegistration == 1:
            api_assert(check_no_service()==0,Breakafterr)
        if TimeofPingCheck != 0:
            api_assert(api1_ping_test("www.baidu.com",TimeofPingCheck),Breakafterr)

        api_writefile("[info]: Switching time is: %s" % resGroup[1])
        
        if resGroup[0] == 0:
            api_writefile("[success]: switch sucess")
            successCount = successCount + 1
        elif resGroup[0] == 1:
            warnCount = warnCount + 1
        else:
            failCount = failCount+1

        
        
        if resGroup[1] <= 30:
            SWDuration1.append(resGroup[1])
        elif resGroup[1] <= 60:
            SWDuration2.append(resGroup[1])
        elif resGroup[1] <= 90:
            SWDuration3.append(resGroup[1])
        elif resGroup[1] <= 120:
            SWDuration4.append(resGroup[1])
        else:
            SWDuration5.append(resGroup[1])

        #Do switch and return duration to the array of SWDuration
        
        api_writefile("Success Count: %s" % successCount)
        api_writefile("Warning Count: %s" % warnCount)
        api_writefile("Fail Count   : %s" % failCount)
        api_writefile("Switching time  0 ~30: %s" % len(SWDuration1))
        api_writefile("Switching time  30~60: %s" % len(SWDuration2))
        api_writefile("Switching time  60~90: %s" % len(SWDuration3))
        api_writefile("Switching time  90~120: %s" % len(SWDuration4))
        api_writefile("Switching time  >120: %s" % len(SWDuration5))

        time.sleep(10)



    
tsc_firmware_switch()
#api1_trigger_switch()
#check_no_service()
