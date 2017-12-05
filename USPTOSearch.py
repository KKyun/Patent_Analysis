import re, requests, time, sys, random
import pandas as pd
import numpy as np

def GooglePatOrg(DataFrameFile):
    GPColumnsDrop = ['inventor/author','publication date','priority date','result link']
    GPColumns = {'id':'PATN','title':'TITLE','assignee':'ASSN','filing/creation date':'FILED','grant date':'GRANTED'}

    GPCompanyName = list(DataFrameFile)[1].split('?assignee=')[1].split('&country=')[0].replace(r'+',' ')
    IndexRenamed = DataFrameFile[0:1].reset_index().as_matrix().tolist()[0]
    DataFrameFile = DataFrameFile[1:].reset_index()
    DataFrameFile.columns = IndexRenamed

    for DropCol in GPColumnsDrop:
        DataFrameFile.drop(DropCol, axis=1, inplace=True)

    DataFrameFile.rename(columns = GPColumns, inplace = True)

    DataFrameFile['PATN'] = DataFrameFile['PATN'].apply(lambda x: int(re.findall('\d+', x)[0]))
    DataFrameFile['FILED'] = DataFrameFile['FILED'].apply(lambda x: int(x[:4]))
    DataFrameFile['GRANTED'] = DataFrameFile['GRANTED'].apply(lambda x: int(x[:4]))

    DataFrameFile = DataFrameFile[DataFrameFile['PATN'] > 2800000]
    DataFrameFile = DataFrameFile[DataFrameFile['GRANTED'] < 2013]

    return(DataFrameFile, GPCompanyName)

def KPIngForm(TotalKeywords, ListofUSPTOFiles, KeywordGVKeyDict):
    ResultDict = {}
    for Files in ListofUSPTOFiles:
        OpenedFile = pd.read_excel(Files)
        OpenedFile.rename(columns={'A': 'PATN', 'B': 'ASSN', 'C':'TITLE','D':'GRANTED'}, inplace=True)
        for Keyword in TotalKeywords:
            USGVKey = KeywordGVKeyDict[Keyword]
            try:
                ResultDict[USGVKey] = pd.concat([ResultDict[USGVKey],OpenedFile[OpenedFile['ASSN'].str.contains(Keyword)]])
            except:
                ResultDict[USGVKey] = OpenedFile[OpenedFile['ASSN'].str.contains(Keyword)]
    return(ResultDict)

def USPTOFrontInfo(PATN, USGVKey):
    while True:
        try:
            USPTOURL = 'http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO1&Sect2=HITOFF&d=PALL&p=1&u=%2Fnetahtml%2FPTO%2Fsrchnum.htm&r=1&f=G&l=50&s1='+str(PATN)+'.PN.&OS=PN/'+str(PATN)+'&RS=PN/'+str(PATN)
            res = requests.get(USPTOURL)
            res.raise_for_status()
        except:
            try:
                time.sleep(random.uniform(0.6,1.2))
                USPTOURL = 'http://patft1.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsearch-bool.html&r=1&f=G&l=50&co1=AND&d=PTXT&s1='+str(PATN)+'.PN.&OS=PN/'+str(PATN)+'&RS=PN/'+str(PATN)
                res = requests.get(USPTOURL)
                res.raise_for_status()
            except:
                time.sleep(random.uniform(1,1.5))
                continue
        Patlocate = res.text.find("<b>United States Patent ")
        if Patlocate == -1:
            time.sleep(random.uniform(3,4))
            continue
        else:
            break
    # First Find CPC List
    CPClocate = res.text.find("CPC Class:")
    if CPClocate == -1:
        if res.text.find('WITHDRAWN')!= -1:
            #Withdrawn Patent. Example: 5001673 (Texas Instruments)
            return({'PATN':PATN, 'GVKey':USGVKey, 'FILED_Source':'No File Date','GRANTED_Source':'WITHDRAWN','ASSN_Source':'WITHDRAWN','CPC':'WITHDRAWN'})
        else:
            # Rare Case USPTO Doesn't Have CPC. Example: 8319552 (Analog Devices)
            print('NO CPC but not Withdrawn')
            return({'PATN':PATN, 'GVKey':USGVKey, 'FILED_Source':'No File Date','GRANTED_Source':'Error','ASSN_Source':'Error','CPC':np.nan})
    else:
        USCPC = res.text[res.text.find(r'">', CPClocate)+2:res.text.find('</TD>',res.text.find(r'">', CPClocate))]
        FDlocate = res.text.find("Filed:")
        if FDlocate == -1:
            #No Full-Text Information Example: 3239754 (Texas Instruments)
            IDlocate = res.text.find(r'Issue Date:')
            if IDlocate==-1:
                USGrant = 'Unavailable'
            else:
                USGrant = int(res.text[res.text.find(r'<b>', IDlocate)+3:res.text.find('</b>',res.text.find(r'<b>', IDlocate))].strip()[-4:])
            return({'PATN':PATN, 'GVKey':USGVKey,'FILED_Source':'No File Date','GRANTED_Source':USGrant,'ASSN_Source':'Unavailable','CPC':USCPC})
        else:
            USFD = int(res.text[res.text.find('<b>',FDlocate)+3:res.text.find('</b>',res.text.find('<b>',FDlocate))].strip()[-4:])
            Assnlocate = res.text.find(r'Assignee:')
            if Assnlocate == -1:
                #Full-Text Information without Assignee. Example: 6587705
                USAssignee = 'No ASSN'
            else:
                #Full-Text Information Example: 5009476 (Texas Instruments)
                USAssignee = ', '.join([x.split('</B>')[0] for x in re.sub(r'\([^)]*\)', '', res.text[res.text.find('<TD',Assnlocate):res.text.find('',res.text.find('</TD>',Assnlocate))]).split('<B>')[1:]])
            USGrant = int(res.text[Patlocate:res.text.find('</TABLE>',Patlocate)].split(r'TD align="right')[-1].split('</b>')[0].strip()[-4:])
            return({'PATN':PATN, 'GVKey':USGVKey, 'FILED_Source':USFD,'GRANTED_Source':USGrant,'ASSN_Source':USAssignee,'CPC':USCPC})

