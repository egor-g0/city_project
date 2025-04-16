import sqlite3
a = 'бузулук'
con = sqlite3.connect("cities.db")
cur = con.cursor()
result = cur.execute(f"""SELECT city FROM cities
            WHERE city LIKE '{a}'""").fetchall()
s = [i[0] for i in result]
print(s)
con.close()