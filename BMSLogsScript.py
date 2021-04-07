import BMSLogsLib as bms

"""Parcourt tous les dossiers récupérer avec la fonction logsOverThreeMonths
Traite les erreurs du dossier de la veille
Écrit les erreurs dans un csv
"""

name = bms.getConfig("boxName")
path = bms.getConfig("path")
dirs = bms.logsOverThreeMonths()
for dir in dirs:
    pathBank = dir+"\\"+dir.strip(path)+"_"+name+"_BBMS_Bank1_minutes.csv"
    pathRack = dir+"\\"+dir.strip(path)+"_"+name+"_BBMS_Bank1_Racks_minutes.csv"
    bms.cleanLogDir(dir, pathBank, pathRack)

errors = bms.checkPreviousDay()
print(errors)
bms.writeLogErrors(errors)
