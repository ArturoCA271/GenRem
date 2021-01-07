import fdb as fb
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import os

###############################################################################
path = 'C:/GenRemision/ConexionDB.txt'
################################################################################
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


def convierteFolio(folio):
    cerosPendientes = 9 - len(folio)
    #print(cerosPendientes)
    if cerosPendientes == 0:
        return folio
    if cerosPendientes > 0:
        serie = ''
        valNumerico = ''; valNumerico = valNumerico.zfill(cerosPendientes )
        for i in folio:
            if '0' <= i <= '9':
                valNumerico = valNumerico + i
            else:
                serie = i
        
        folio = serie.upper() + valNumerico
        return folio


def GeneraFolio(cursor):
    SQL = '''SELECT F.serie, F.consecutivo
            FROM FOLIOS_VENTAS F
            WHERE  F.folio_ventas_id = 1966'''
    cursor.execute(SQL)
    row = cursor.fetchone()
    serie, consecutivo = row[0], row[1]
    folio = serie + str(consecutivo)
    folio = convierteFolio(folio)
    #Pendiente de actualizar folio
    #print(consecutivo)
    consecutivo += 1
    #print(consecutivo)
    SQL = 'UPDATE FOLIOS_VENTAS F SET F.consecutivo = {} WHERE F.folio_ventas_id = 1966'.format(consecutivo)
    cursor.execute(SQL)
    return folio

def GetIdDocto(con, cursor):
    SQL = 'GEN_DOCTO_ID'
    cursor.callproc(SQL)
    id = cursor.fetchone()
    con.commit()
    return id[0]

def LlenaImportesDoctos(cursor, folioRM):
    SQL = '''SELECT DCOMP.importe_neto, DCOMP.total_impuestos, DCOMP.almacen_id, DCOMP.docto_cm_id
        FROM doctos_cm DCOMP
        WHERE DCOMP.folio LIKE '{}' '''.format(folioRM)
    cursor.execute(SQL)
    return cursor.fetchone()

def InsertaValor(id, cursor):
    SQL = """INSERT INTO RM_convertidos(docto_id)
            VALUES({})""".format(id)
    
    cursor.execute(SQL)

##############Ejecucion###########################################################


def CreadoRemision(con, folio):

    cursor = CursorSql(con)
    folioRM = folio
    folioRM = convierteFolio(folioRM)#CONVIERTE FOLIO A FORMATO DE 9 DIGITOS

    ################llenado de variables ################

    try:
        totalImporteNeto, totalImpuestos, almacen, Docto_cm_id = LlenaImportesDoctos(cursor, folioRM)
    except:
        messagebox.showinfo(" Folio inexistente ")
        return
        

    #######################  VERIFICA SI EXISTE EL DOCUMENTO  ########################################
    SQL = """SELECT RM.docto_id 
            FROM RM_convertidos RM
            WHERE RM.docto_id = {}""".format(Docto_cm_id)

    cursor.execute(SQL)
    existe = cursor.fetchone()

    if existe:
        messagebox.showinfo(" La RM ya fue generada ")
        cursor.close()
        con.commit()

    else:
        now = datetime.now()
        fecha = str(now.year) + '-' + str(now.month) + '-' + str(now.day) 
        hora = str(now.hour) + ':' + str(now.minute)

        folioREM = GeneraFolio( cursor)
        IdDocto = GetIdDocto(con, cursor)
        print('Si no existe el id')
        ########################   CREACION  DE REMISION    ############################
        SQL = """INSERT INTO  DOCTOS_VE (DOCTO_VE_ID, TIPO_DOCTO, SUCURSAL_ID, FOLIO, FECHA, HORA, CLIENTE_ID, DIR_CLI_ID, MONEDA_ID, COND_PAGO_ID, IMPORTE_NETO, TOTAL_IMPUESTOS, DIR_CONSIG_ID, SISTEMA_ORIGEN, CLAVE_CLIENTE, ALMACEN_ID, ESTATUS, LUGAR_EXPEDICION_ID)
                VALUES ( {}, 'P', 24518,  '{}' ,'{}', '{}', 21659,  21662, 1, 1700, {}, {}, 21662, 'VE', 'KMX170327JP7', {}, 'P', 235) """.format(IdDocto, folioREM, fecha, hora, totalImporteNeto, totalImpuestos, almacen)
        cursor.execute(SQL)


        SQL = """SELECT CDET.clave_articulo ,CDET.articulo_id, CDET.unidades, CDET.precio_unitario, CDET.pctje_dscto, CDET.precio_total_neto
                FROM doctos_cm DCOMP
                INNER JOIN doctos_cm_det CDET ON( DCOMP.docto_cm_id = CDET.docto_cm_id)
                WHERE DCOMP.folio LIKE '{}' """.format(folioRM)

        cursor.execute(SQL)

        for row in cursor.fetchall():
            Docto_ve_det_id = GetIdDocto(con, cursor)
            SQL = """INSERT INTO DOCTOS_VE_DET (DOCTO_VE_DET_ID, DOCTO_VE_ID, CLAVE_ARTICULO, ARTICULO_ID, UNIDADES, UNIDADES_SURT_DEV, UNIDADES_A_SURTIR, PRECIO_UNITARIO, PCTJE_DSCTO, PRECIO_TOTAL_NETO, ROL)
                VALUES ({}, {}, '{}', {}, {}, 0, {}, {}, {}, {}, 'N')""".format(Docto_ve_det_id, IdDocto, row[0], row[1], row[2], row[2], row[3], row[4], row[5])
            cursor.execute(SQL)

        ##################  APLICACION DE REMISION  ########################
        Lista = []
        Lista.append(IdDocto)
        cursor.callproc('APLICA_DOCTO_VE', Lista)
        con.commit()

        ################################################################################

        InsertaValor(Docto_cm_id, cursor)
        con.commit()
        cursor.close()
        messagebox.showinfo("Pedido {} generado con exito".format(folioRM))


#LIMPIADO Y ENVIO DE DATOS
def envioDatosLimpiado():
    folio = entradaFolio.get()
    CreadoRemision(con,  folio)
    entradaFolio.delete(0, 'end')


main = tk.Tk()
main.title("Principal")
main.geometry('520x480') 
menubar = tk.Menu(main)
entradaFolio = tk.Entry(main, bd = 5)
entradaFolio.pack()
con = creaConexionDB()
botonEnvio = tk.Button(main, text="Generar", height="3", width="15", command = envioDatosLimpiado)
botonEnvio.pack()


main.config(menu=menubar)#asignacion del menu a la base

#Agregados de submenus
filemenu = tk.Menu(menubar, tearoff=0)#elegir que opcion realizar
#agregado de submenus a la barra
menubar.add_cascade(label="Archivo", menu=filemenu)
filemenu.add_separator()
filemenu.add_command(label="Salir", command=main.quit)
main.mainloop()