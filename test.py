import csv

with open("C:\\Users\\admin\\Desktop\\BBMS_Logs\\20201203\\GridBSM_Bank1_20201203.csv", 'r') as r:
    csv_read = csv.reader(r, delimiter=',')
    for row in csv_read:
        print(row)