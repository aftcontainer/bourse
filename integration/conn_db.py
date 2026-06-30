import oracledb

connection1 = oracledb.connect(
    user="BOURUSER",
    password="Afri2012",
    host="192.168.1.102",
    port=1521,
    service_name="BOURSE"
)

connection2 = oracledb.connect(
    user="bourseDBAdmin",
    password="bourseDB2026",
    host="192.168.1.209",
    port=1521,
    service_name="XEPDB1"
)

cursor1 = connection1.cursor()
cursor2 = connection2.cursor()

cursor1.execute("SELECT * FROM DEVISE")

for row in cursor1:
    cursor2.execute("""INSERT INTO DEVISE""")
    print(row)

cursor1.close()
connection1.close()