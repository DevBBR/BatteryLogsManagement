import json
import subprocess
from datetime import datetime
from datetime import timedelta
import os
import csv
#import pymysql


def checkIfProcessRunning(processName):
    """Utilise la librairie subprocess pour vérifier
     si le processus passé en paramètre est en focntionnement

    Args:
        processName (string): chaine de caractères du processus recherché

    Returns:
        string: Renvoie la string du processus s'il est trouvé et None sinon
    """
    command = 'tasklist', '/fi', 'imagename eq %s.*' % processName, '/fo', 'csv', '/nh'
    output = subprocess.check_output(command).decode("utf-8", errors="ignore")
    output = output.split(',')
    print(output[0])
    return processName in output[0]
    
def isWampRunning():
    """Appelle la fonction checkIfProcessRunning avec les deux processus concernant wamp

    Returns:
        booléen: Renvoie True si les deux processus sont trouvés et False sinon
    """
    if not checkIfProcessRunning("mysqld") or not checkIfProcessRunning("httpd"):
        return False
    return True

def getDate(delta, augment=0):
    """Fonction pour récupérer la date en appliquant un delta et en 
    choisissant entre deux formats : diminué ou augmenté

    Args:
        delta (int): nombre de jours d'écart à appliquer à la date courante
        augment (int, optional): passer 1 pour le format augmenté. Defaults to 0.

    Returns:
        string: Chaine de caractère contenant la date demandée
    """
    TIME_FORMAT_REDUCED = '%Y%m%d'
    TIME_FORMAT_AUGMENTED = '%Y-%m-%d %H:%M:%S'
    timeFormat = (TIME_FORMAT_AUGMENTED if augment else TIME_FORMAT_REDUCED)
    timestamp = datetime.today()
    d1 = timestamp - timedelta(delta)
    d1 = d1.strftime(timeFormat)
    return d1

def renameLogsDir():
    """Renomme les fichiers dans les dossiers antérieurs à la veille du jour courant
    Cette fonction est utilisée à l'initialisation
    """
    path = getConfig("path")
    name = getConfig("boxName")
    date = getDate(2)
    i = 0
    for root, dirs, files in os.walk(path):
        if not i:
            i+=1
            continue
        dir = root.strip(path)
        if dir <= date:
            for file in files:
                if file.startswith("GridBSM_Bank1"):
                    os.rename(root+"\\"+file, root+"\\"+name+"_"+file)
                elif not file.startswith("GridBSM_Event"):
                    os.remove(root+"\\"+file)
            #os.rename(root, root.strip(dir)+"\\"+name+"_"+dir.strip("\\"))

def getConfig(param):
    """Récupère la données du fichier config.json avec le nom passé en paramètre

    Args:
        param (string): clé correspondant à la valeur demandé dans le fichier json

    Returns:
        string: valeur correspondant à la clé dans le fichier json
    """
    configPath = os.path.dirname(os.path.realpath(__file__))
    with open(configPath+"\\config.json", "r") as file:
        data = json.load(file)
        return data[param]

def logsOverThreeMonths():
    """Récupère les noms des dossiers de logs antérieures à 3 mois par rapport à la date courante

    Returns:
        tab[string]: tableau contenant tous les noms de dossiers concernés par la recherche
    """
    okdirs = []
    path = getConfig("path")
    name = getConfig("boxName")
    date = getDate(90)
    i = 0
    for root, dirs, files in os.walk(path):
        if not i:
            i+=1
            continue
        dir = root.strip(path)
        if dir <= date:
            print(dir)
            okdirs.append(root)
    return okdirs

def addMinutesRow(file, path, count):
    """Parcourt un fichier et rajoute les données minutes à un fichier minute dans le même dossier
    Si le fichier minute n'existe pas encore il est créé avec les headers csv correctes

    Args:
        file (string): chaine de caractères correspondant au fichier à parcourir
        path (string): chaine de caractères correspondant au fichier minute dans lequel rajouter les données
        count (int): compteur pour ajouter le bon index de ligne au csv

    Returns:
        int: le compteur est renvoyé pour reprendre le compte à partir de la dernière exécution
    """
    i = 0
    with open(path, 'a', newline='') as w:
        print(file)
        if os.stat(path).st_size == 0:
            empty = 1
        else:
            empty = 0
        csv_write = csv.writer(w, delimiter=',')
        with open(file, 'r') as r:
            csv_read = csv.reader(r, delimiter=',')
            for row in csv_read:
                if empty and i < 6:
                    csv_write.writerow(row)
                    i+=1
                    continue
                elif not empty and i < 6:
                    i+=1
                    continue

                if row[1].endswith(':00'):
                    count+=1
                    row[0] = count
                    csv_write.writerow(row)
    return count

def cleanLogDir(dir, pathBank, pathRack):
    """Parcourt le dossier entier à la recherche des fichiers seconde pour les traiter
    avec la fonction addMinutesRow
    Permet également de supprimer les fichiers résiduels

    Args:
        dir (string): chemin vers le dossier à parcourir
        pathBank (string): chemin vers le fichier minute pour le bank BBMS
        pathRack (string): chemin vers le fichier minute pour les racks RBMS
    """
    name = getConfig("boxName")
    path = getConfig("path")
    _, _, files = next(os.walk(dir))
    countLinesBank = 0
    countLinesRack = 0
    for file in files:
        if file.startswith(name+"_GridBSM_Bank1_"):
            countLinesBank = addMinutesRow(dir+"\\"+file, pathBank, countLinesBank)
        elif file.startswith(name+"_GridBSM_Bank1Racks_"):
            countLinesRack = addMinutesRow(dir+"\\"+file, pathRack, countLinesRack)

        if not file.startswith("GridBSM_Event") and not file.startswith(dir.strip(path)):
            os.remove(dir+"\\"+file)

def checkErrorsOnFile(file, count):
    """Parcourt un fichier csv seconde pour relever les différentes erreurs d'écriture de log

    Args:
        file (string): chemin vers le fichier à parcourir
        count (int): compteur pour connaître le nombre de lignes écrites pour BBMS et RBMS

    Returns:
        int, int: compteur de lignes et nombre de fautes renvoyés pour le suivi
    """
    i = 0
    fault = 0
    with open(file, 'r') as r:
        csv_read = csv.reader(r, delimiter=',')
        for row in csv_read:
            if i < 6:
                i+=1
                continue
            count+=1
            if row[3] == "Fault" or row[29] == 0:
                fault += 1
    return count, fault

def checkPreviousDay():
    """Parcourt le dossier de la veille pour traiter les erreurs potentiels dans un Dict et
    fait le tri en supprimmant les fichiers résiduels et en renommant les fichiers utiles

    Returns:
        Dict: Dictionnaire python contenant les erreurs rencontrées pendant le parcours des fichiers seconde de la veille
    """

    errors = {
        "time": getDate(0, augment=1),
        "wampError":0, 
        "noDir": 1,
        "noLogFiles": 1,
        "noEnoughWriting": 0,
        "notEnoughLines": 0,
        "lastDayNbLines": 0,
        "lastDayFaults": 0
    }

    errors = runningWamp(errors)

    date = getDate(1)
    path = getConfig("path")
    name = getConfig("boxName")
    newPath = path+"\\"+date
    countLines = 0
    nbFault = 0

    if os.path.exists(path+"\\"+date):
        errors["noDir"] = 0
    else:
        return errors
    
    #os.rename(path+"\\"+date, newPath)
    _, _, files = next(os.walk(newPath))
    print(files)
    for file in files:
        if file.startswith("GridBSM_Bank1_"):
            errors["noLogFiles"] = 0
            countLines, fault = checkErrorsOnFile(newPath+"\\"+file, countLines)
            nbFault += fault
        if not file.startswith("GridBSM_Event"):
            os.rename(newPath+"\\"+file, newPath+"\\"+name+"_"+file)
    if countLines < 82800:
        errors["notEnoughLines"] = 1
    errors["lastDayNbLines"] = countLines
    if nbFault > 3600:
        errors["notEnoughWriting"] = 1
    errors["lastDayFaults"] = nbFault
    return errors

def runningWamp(errors):
    """Relance le processus wamp s'il n'est pas en marche
    Si une exception est levée au lancement de wamp alors une erreur est renvoyé 

    Args:
        errors (Dict): Dictionnaire python contenant les différentes erreurs à notifier

    Returns:
        Dict: Dictionnaire python mis à jour s'il y a une erreur au lancement de wamp
    """
    if isWampRunning():
        print("wamp is running")
    else:
        print("wamp is not running")
        try:
            subprocess.Popen(["C:\\wamp64\\wampmanager.exe"])
        except Exception as e:
            errors["wampError"] = 1
        print("lancement de wamp")
    return errors

"""def dbConnect():
    name = getConfig("boxName")
    try:
        connexion = pymysql.connect(
                    host="localhost",
                    user="root",
                    password="",
                    db=name,
                    autocommit=True,
                    cursorclass=pymysql.cursors.DictCursor)

        with connexion.cursor() as cursor:
            requete = "INSERT INTO `alarmhistory`(`Al_Start_Time`,
              `Al_Start_Time_ms`,
              `Al_Tag`,
              `Al_Message`,
              `Al_Ack`,
              `Al_Active`,
              `Al_Tag_Value`,
              `Al_Prev_Tag_Value`, `Al_Group`, `Al_Priority`, `Al_Selection`, `Al_Type`, `Al_Ack_Req`, `Al_Norm_Time`, `Al_Norm_Time_ms`, `Al_Ack_Time`, `Al_Ack_Time_ms`, `Al_User`, `Al_User_Comment`, `Al_User_Full`, `Al_Station`, `Al_Deleted`, `Last_Update`, `Last_Update_ms`) VALUES ([value-1],[value-2],[value-3],[value-4],[value-5],[value-6],[value-7],[value-8],[value-9],[value-10],[value-11],[value-12],[value-13],[value-14],[value-15],[value-16],[value-17],[value-18],[value-19],[value-20],[value-21],[value-22],[value-23],[value-24])"
            cursor.execute(requete)
            result = cursor.fetchall()
            print(result)
            lenQuery = len(result)

    except Exception as e:
        print("Exception à la connexion à la base" + str(e))
    finally:
        if connexion is not None:
            connexion.close()
    #"""

def initLogErrors(file, errors):
    """Initialise le fichiers csv traçant les erreurs de logs quotidiennes

    Args:
        file (string): chemin vers le fichier à créer
        errors (Dict): Dictionnaire utilisé pour récupérer les clés afin d'initialiser les headers csv
    """
    with open(file, 'w', newline='') as csvfile:
        fieldnames = errors.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

def writeLogErrors(errors):
    """Écrit les erreurs quotidiennes dans le fichier csv 

    Args:
        errors (Dict): Dict contenant les erreurs à écrire
    """
    file = getConfig("aveva")+"\\logErrors.csv"
    if not os.path.exists(file):
        initLogErrors(file, errors)
    
    with open(file, 'a', newline='') as csvWrite:
        writer = csv.DictWriter(csvWrite, fieldnames=errors.keys())
        writer.writerow(errors)
