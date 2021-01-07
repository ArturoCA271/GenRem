import fdb as fb
import os

###############################################################################
path = 'C:/GenRemision/ConexionDB.txt'
###############################################################################


def creaConexionDB():
    conexion = []
    archivo = open(path, 'r')
    for i in archivo:
        conexion.append(i)
    archivo.close()
    #print(" ")
    val = len(conexion[0]) -1
    miHost = conexion[0][5:val]

    val = len(conexion[1]) - 1
    DB = conexion[1][5:val]

    val = len(conexion[2]) -1
    us = conexion[2][3:val]

    val = len(conexion[3])
    passw = conexion[3][6:val]
    return (fb.connect(host = miHost, database = DB, user = us, password = passw)) 

def CursorSql(con):
    return (con.cursor())


def CreacionTablaRecpMerca(cursor):
    SQL = '''create table RM_convertidos
            (
            docto_id integer not null

            ); '''
    cursor.execute(SQL)
    print('Creando trabla')

con = creaConexionDB()
cursor = CursorSql(con)
CreacionTablaRecpMerca(cursor)
con.commit()