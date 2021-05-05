import BMSLogsLib as bms

"""Parcourt tous les dossiers récupérer avec la fonction logsOverThreeMonths
Traite les erreurs du dossier de la veille
Écrit les erreurs dans un csv
"""

name = bms.getConfig("boxName")
path = bms.getConfig("path")
"""Passez en paramètre le nombre de jour avec les secondes à conserver (90 = 3 mois)"""
dirs = bms.logsOverDate(90)
for dir in dirs:
    pathBank = dir+"\\"+name+"_"+dir.strip(path)+"_BBMS_Bank1_minutes.csv"
    pathRack = dir+"\\"+name+"_"+dir.strip(path)+"_BBMS_Bank1_Racks_minutes.csv"
    bms.cleanLogDir(dir, pathBank, pathRack)

errors = bms.checkPreviousDay()
print(errors)
bms.writeLogErrors(errors)
