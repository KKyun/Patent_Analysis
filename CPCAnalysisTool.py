import re, requests, time, sys
import pandas as pd
import numpy as np

def FindCPCDef(CPCList):
    Result = []
    MainGroupDict = {}
    SubclassList = [x.strip() for x in CPCList if r' ' not in x or len(x)==5]    
    MainGroupList = [x.split(r'/')[0]+r'/' for x in CPCList if x not in SubclassList]
    if len(MainGroupList)!=0:
        for MainGroup in MainGroupList:
            Subclass = MainGroup[:4]
            if ' ' in Subclass:
                print('Problem with Maingroup ', MainGroup)
                sys.exit()
            MainGroupDict[MainGroup] = Subclass
        TotalSubList = list(set(SubclassList + [x for x in list(MainGroupDict.values())]))
    else:
        TotalSubList = list(set(SubclassList))
    for Subclass in TotalSubList:
        try:
            defURL = r'https://www.uspto.gov/web/patents/classification/cpc/html/def'+str(Subclass)+'.html'
            res = requests.get(defURL)
            res.raise_for_status()
        except:
            try:
                time.sleep(random.uniform(3,4))
                defURL = r'https://www.uspto.gov/web/patents/classification/cpc/html/def'+str(Subclass)+'.html'
                res = requests.get(defURL)
                res.raise_for_status()
            except:
                print(Subclass)
                continue
        CPClocate = 0
        print(MainGroupList)
        if len(MainGroupList)!=0:
            for section in range(len(res.text.split(r'<div class=defTitle>'))):
                CPClocate = res.text.find(r'<div class=defTitle>', CPClocate+1)
                CPClocatend = res.text.find(r'</div>', CPClocate)
                Description = res.text[CPClocate+len('<div class=defTitle>'):CPClocatend].lower()
                Description = re.sub("([\(\[]).*?([\)\]])", "\g<1>\g<2>", Description)
                CPCCodelocate = res.text.find(r'>'+Subclass,CPClocate-50)
                if CPCCodelocate>CPClocate:
                    print(Subclass)
                    continue
                CPCCodelocatend = res.text.find(r'</a>',CPCCodelocate)
                Maingroup = res.text[CPCCodelocate+1:CPCCodelocatend].replace(r'&nbsp;', r' ')
                if (Maingroup != Subclass) and (Maingroup[-3:]!=r'/00'):
                    continue
                Maingroup = Maingroup.split(r'/')[0]+r'/'
                if (Maingroup != Subclass) and (Maingroup not in MainGroupList):
                    continue
                Result.append({'Subclass':Subclass, 'Description': Description, 'Maingroup':Maingroup})
        else:
            CPClocate = res.text.find(r'<div class=defTitle>', CPClocate+1)
            CPClocatend = res.text.find(r'</div>', CPClocate)
            Description = res.text[CPClocate+len('<div class=defTitle>'):CPClocatend].lower()
            Description = re.sub("([\(\[]).*?([\)\]])", "\g<1>\g<2>", Description)
            CPCCodelocate = res.text.find(r'>'+Subclass,CPClocate-50)
        Result.append({'Subclass':Subclass, 'Description': Description, 'Maingroup':Subclass})
    return(pd.DataFrame(Result))

def FirstCPCList(DataFrameFile):
    CPCColum = [x for x in list(DataFrameFile.columns) if x.startswith('CPC')]
    return(DataFrameFile[CPCColum[0]].apply(lambda x:x.split(r'); ')[0].split(r'/')[0] + r'/'))
    #return(DataFrameFile[CPCColum[0]].apply(lambda x:x.split(r'); ')[0].split(r' ')[0]+r' '))

def RatioFinder(DataFrameFile, CPCList):
    ResultFile = []
    TotNum = len(DataFrameFile.index)
    if 'FirstCPC' in list(DataFrameFile.columns):
        for CPCCode in CPCList:
            ResultFile.append({'CPC': CPCCode, 
                               'Count':len(DataFrameFile[DataFrameFile['FirstCPC'].str.contains(CPCCode)].index),
                               'Ratio':len(DataFrameFile[DataFrameFile['FirstCPC'].str.contains(CPCCode)].index)/TotNum*100})
    else:
        for CPCCode in CPCList:
            ResultFile.append({'CPC': CPCCode, 
                               'Count':len(DataFrameFile[DataFrameFile['CPC'].str.contains(CPCCode)].index),
                               'Ratio':len(DataFrameFile[DataFrameFile['CPC'].str.contains(CPCCode)].index)/TotNum*100})
    ResultFile = pd.DataFrame(ResultFile)
    ResultFile = ResultFile[ResultFile['CPC'].str.len() < 15]
    ResultFile.sort_values(by=['Ratio'], ascending=[False], inplace=True)
    return(ResultFile)

def CumuFinder(DataFrameFile, CPCList):
    ResultFile = []
    TotNum = len(DataFrameFile.index)
    DataFrameFile['Test'] = np.nan
    for CPCCode in CPCList:
        DataFrameFile['Test'] = np.where(DataFrameFile['CPC'].str.contains(CPCCode), 1, DataFrameFile['Test'])
    
    return(DataFrameFile['Test'].count(), DataFrameFile['Test'].count()/TotNum*100)
    
def SavingFile(FolderPath, DataFile):
    writer = pd.ExcelWriter(CPCAnalysisPath+r'\06_'+CompName+r'('+str(USGVKey)+str(r')')+'.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()


def GetUSGVKey(filename):
    if r').xls' in filename[-6:]:
        USGVkey = int(filename.split(r'(')[1].split(r').xls')[0])
    else:
        USGVkey = 0
    return(USGVkey)

def GetYear(DataFrameFile, OldColName, NewColName):
    DataFrameFile[NewColName] = DataFrameFile[OldColName].apply(lambda x: int(x[-4:]))
    return(DataFrameFile[NewColName])
