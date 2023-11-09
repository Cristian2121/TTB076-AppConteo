"""
    Título del proyecto: SIGyC
    Descripción del proyecto: Trabajo de titulación.
    Autor: Cristian Del Angel Fiscal
    Fecha: 22/07/2023
    Licencia: Ninguna

    Librerías:
    tkinter: Kit de herramientas GUI.
    PIL: Procesamiento de imágenes directamente en python.
    mysql: Primitivas para trabajar con bases de datos.
    datetime: Obtener fecha y hora del ordenador.
    cv: Ejecutar modelos de reconocimiento de objetos.
"""
import os
import sys

import mysql.connector

import numpy as np
import cv2 as cv
import imutils

from datetime import datetime

from tkinter import *
from tkinter import ttk
from tkinter import messagebox

from PIL import ImageTk, Image

class Main():
    """
        Interfaz Gráfica de Usuario que permite elegir algún tipo de pan
        y posteriormente procesarlo para realizar su conteo y captura de datos.
    """

    def __init__(self, raiz) -> None:
        """
            Constructor de la clase.

            Parámetros:
            raiz: Widget principal de la GUI
        """

        self.raiz = raiz
        self.raiz.title('Aplicación de conteo')
        self.raiz.resizable(0, 0)
        self.raiz.protocol("WM_DELETE_WINDOW", self.cerrar_app)
        
        #-------------------MARCOS----------------------
        self.frm_acceso = ttk.Frame(self.raiz)
        self.frm_seleccion = ttk.Frame(self.raiz)
        self.frm_formulario = ttk.Frame(self.raiz)
        self.frm_supervision = ttk.Frame(self.raiz)
        self.frm_resumen = ttk.Frame(self.raiz)

        self.ventana_acceso()

        #-------------------VARIABLES GLOBALES----------------------
        self.rd_elegido = StringVar(value="Dona")
        self.id_usuario = None
        self.usuario_operador = StringVar()
        self.descripcion = StringVar()
        self.fecha = StringVar()
        self.hora_inicio = StringVar()
        self.hora_termino = StringVar()
        self.conteo = 0
        self.contador_retraso = 0

        #-------------------VARIABLES DEL MODELO------------------------
        self.red = cv.dnn.readNetFromONNX(self.ruta_recurso('best.onnx'))
        archivo = open(self.ruta_recurso('yolov3.txt'), 'r')
        self.clases = archivo.read().split('\n')
        self.tracker = cv.TrackerKCF_create()
        self.bbox = None

        #-------------------VARIABLE DEL CAPTURADOR DE VIDEO------------------------
        self.cap = None

    def cerrar_app(self) -> None:
        """
            Permite detener la ejecución de la aplicación en cualquier ventana que se encuentre
            el usuario.
        """

        respuesta = messagebox.askokcancel("Salir", "¿Está seguro de salir de la aplicación?")

        if respuesta:
            self.raiz.destroy()

    def ruta_recurso(self, ruta_relativa) -> str:
        """
            Obtiene la ruta absoluta del recurso.

            Parámetros:
            ruta_relativa: nombre del archivo que se desea abrir.

            Retorno:
            Cadena que contiene la ruta absoluta que apunta al archivo.
        """

        ruta_base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(ruta_base, ruta_relativa)

    def ventana_acceso(self) -> None:
        """
            Interfaz que muestra el inicio de sesión.
        """

        self.frm_acceso.pack()
        self.frm_resumen.pack_forget()

        self.raiz.geometry('250x250')
        
        l_texto = ttk.Label(self.frm_acceso, text='ACCESO')
        l_texto.config(font=('Helvatical bold',20))
        l_texto.grid(row=0, column=0, padx=5, pady=10)
        l_usuario = ttk.Label(self.frm_acceso, text='Usuario', font=5)
        l_usuario.grid(row=1, column=0, sticky='w', padx=5, pady=2)
        l_contrasenia = ttk.Label(self.frm_acceso, text='Contraseña', font=5)
        l_contrasenia.grid(row=3, column=0, sticky="w", padx=5, pady=2)

        self.e_usuario = ttk.Entry(self.frm_acceso, font=5, justify="center")
        self.e_usuario.grid(row=2, column=0, padx=5, pady=10)
        self.e_contrasenia = ttk.Entry(self.frm_acceso, font=5, justify="center", show="*")
        self.e_contrasenia.grid(row=4, column=0, padx=5, pady=10)

        btn_ingresar = ttk.Button(self.frm_acceso, text="Acceder", command=lambda:self.validar_datos(self.e_usuario.get(), self.e_contrasenia.get()))
        btn_ingresar.grid(row=5, column=0, padx=5, pady=10)

    def validar_datos(self, usuario, contrasenia) -> None:
        """
            Función encargada de validar los datos de inicio de sesión con los datos
            almacenados en la base de datos.

            Parámetros:
            usuario: cadena que contiene el nombre de usuario.
            contrasenia: cadena que contiene la contraseña del usuario.
        """

        if usuario == "" or contrasenia == "":
            messagebox.showerror('Formulario', "Debe llenar todos los campos, por favor.")
            self.e_usuario.delete(0, END)
            self.e_contrasenia.delete(0, END)
        else:
            operacion = ("SELECT * FROM usuarios WHERE usuario=%s AND contrasenia=%s")
            parametros = (usuario, contrasenia)

            try:
                cnx = mysql.connector.connect(
                    user='root',
                    password='root',
                    host='localhost',
                    database='tt_prueba1'
                )
                cursor = cnx.cursor()
                cursor.execute(operacion, parametros)
                registro = cursor.fetchall()[0]
                cnx.commit()

                if registro:
                    self.usuario_operador = usuario
                    self.id_usuario = registro[0]
                    self.ventana_seleccion()
            except:
                messagebox.showerror('BD', "No se encontró el usuario")
                self.e_usuario.delete(0, END)
                self.e_contrasenia.delete(0, END)
            finally:
                cursor.close()
                cnx.close()

    def ventana_seleccion(self) -> None:
        """
            Interfaz que muestra la ventana donde se puede elegir la pieza de pan.
        """

        self.frm_seleccion.pack()
        self.frm_acceso.pack_forget()
        self.frm_resumen.pack_forget()
        self.frm_formulario.pack_forget()

        self.raiz.geometry('800x350')
        
        l_saludo = ttk.Label(self.frm_seleccion, text='BIENVENIDO: ' + self.usuario_operador)
        l_saludo.config(font=('Helvatical bold',20))
        l_saludo.grid(row=0, column=0, padx=5, pady=10, columnspan=3)
        l_texto = ttk.Label(
            self.frm_seleccion, 
            text='Por favor, marque la pieza de pan que desea procesar y luego presione el botón siguiente.', 
            font=5
        )
        l_texto.grid(row=1, column=0, sticky='w', padx=5, pady=2, columnspan=3)

        # Referencia y escalado de imágen de portada
        img = ImageTk.PhotoImage(Image.open(self.ruta_recurso('b076_dona.jpg')).resize((80, 80)))
        lbl_img = ttk.Label(self.frm_seleccion, image=img)
        lbl_img.grid(row=2, column=0)
        img2 = ImageTk.PhotoImage(Image.open(self.ruta_recurso('b076_concha.jpg')).resize((80, 80)))
        lbl_img2 = ttk.Label(self.frm_seleccion, image=img2)
        lbl_img2.grid(row=2, column=1)
        img3 = ImageTk.PhotoImage(Image.open(self.ruta_recurso('b076_azucarado.jpg')).resize((80, 80)))
        lbl_img3 = ttk.Label(self.frm_seleccion, image=img3)
        lbl_img3.grid(row=2, column=2)
        img4 = ImageTk.PhotoImage(Image.open(self.ruta_recurso('b076_ombligo.jpg')).resize((80, 80)))
        lbl_img4 = ttk.Label(self.frm_seleccion, image=img4)
        lbl_img4.grid(row=4, column=0)
        img5 = ImageTk.PhotoImage(Image.open(self.ruta_recurso('b076_oreja.jpg')).resize((80, 80)))
        lbl_img5 = ttk.Label(self.frm_seleccion, image=img5)
        lbl_img5.grid(row=4, column=1)

        # Se necestia hacer referencia a la imágen, ya que si no es borrada de memoría
        lbl_img.image = img
        lbl_img2.image = img2
        lbl_img3.image = img3
        lbl_img4.image = img4
        lbl_img5.image = img5

        r1 = ttk.Radiobutton(self.frm_seleccion, text='Dona', variable=self.rd_elegido, value='Dona')
        r1.grid(row=3, column=0, padx=5, pady=5)
        r2 = ttk.Radiobutton(self.frm_seleccion, text='Concha', variable=self.rd_elegido, value='Concha')
        r2.grid(row=3, column=1, padx=5, pady=5)
        r3 = ttk.Radiobutton(self.frm_seleccion, text='Azucarado', variable=self.rd_elegido, value='Azucarado')
        r3.grid(row=3, column=2, padx=5, pady=5)
        r4 = ttk.Radiobutton(self.frm_seleccion, text='Ombligo', variable=self.rd_elegido, value='Ombligo')
        r4.grid(row=5, column=0, padx=5, pady=5)
        r5 = ttk.Radiobutton(self.frm_seleccion, text='Oreja', variable=self.rd_elegido, value='Oreja')
        r5.grid(row=5, column=1, padx=5, pady=5)

        btn_siguiente = ttk.Button(self.frm_seleccion, text="Siguiente", command=lambda:self.ventana_formulario())
        btn_siguiente.grid(row=6, column=1, padx=5, pady=5)

    def ventana_formulario(self) -> None:
        """
            Interfaz que muestra una ventana con información de la pieza de pan elegida,
            además del campo para dar una descripción.
        """

        self.frm_formulario.pack()
        self.frm_seleccion.pack_forget()
        self.frm_supervision.pack_forget()

        self.raiz.geometry('500x300')

        pza_pan = self.rd_elegido.get()

        # Se eliminan los anteriores widgets para evitar superponer información
        for widget in self.frm_formulario.winfo_children():
            widget.destroy()

        l_descripcion = ttk.Label(self.frm_formulario, text='Ingrese una descripción de la operación')
        l_descripcion.config(font=('Helvatical bold',20))
        l_descripcion.grid(row=0, column=0, padx=5, pady=10, columnspan=2)
        self.l_pieza = ttk.Label(self.frm_formulario, text=f'Pieza de pan: {pza_pan}', font=5)
        self.l_pieza.grid(row=1, column=0, sticky='w', padx=5, pady=5, columnspan=2)
        l_usuario = ttk.Label(self.frm_formulario, text=f'Usuario operador: {self.usuario_operador}', font=5)
        l_usuario.grid(row=2, column=0, sticky='w', padx=5, pady=5, columnspan=2)
        l_descripcion = ttk.Label(self.frm_formulario, text='Descripción:', font=5)
        l_descripcion.grid(row=3, column=0, sticky="w", padx=5, pady=5, columnspan=2)

        self.t_descripcion = Text(self.frm_formulario, width=60, height=5)
        self.t_descripcion.grid(row=4, column=0, padx=5, pady=5, columnspan=2)

        btn_siguiente = ttk.Button(self.frm_formulario, text="Siguiente", command=lambda:self.procesar_formulario())
        btn_siguiente.grid(row=5, column=0, padx=5, pady=5)

        btn_regresar = ttk.Button(self.frm_formulario, text="Regresar", command=lambda:self.ventana_seleccion())
        btn_regresar.grid(row=5, column=1, padx=5, pady=5)

    def procesar_formulario(self) -> None:
        """
            Función encargada de verificar que el campo de descripción no este vacío,
            además de asignar datos referentes a la fecha y hora del conteo.
        """

        self.descripcion = self.t_descripcion.get("1.0", "end-1c")
        
        if self.descripcion == "":
            messagebox.showerror("Formulario", "No se relleno el campo requerido.")
        else:
            ahora = datetime.now()
            self.fecha = ahora.strftime("%Y-%m-%d")
            self.hora_inicio = ahora.strftime("%H:%M:%S")
            self.ventana_supervision()

    def ventana_supervision(self) -> None:
        """
            Interfaz encargada de mostrar el capturador de video y el conteo.
        """

        self.frm_supervision.pack()
        self.frm_formulario.pack_forget()

        self.raiz.geometry('500x450')

        self.l_video = ttk.Label(self.frm_supervision)
        self.l_video.grid(row=0, column=0, columnspan=2)

        self.btn_iniciar = ttk.Button(self.frm_supervision, text="Iniciar", command=lambda:self.iniciar_video())
        self.btn_iniciar.grid(row=2, column=0, padx=5, pady=5)

        self.btn_regresar = ttk.Button(self.frm_supervision, text="Regresar", command=lambda:self.ventana_formulario())
        self.btn_regresar.grid(row=2, column=1, padx=5, pady=5)

        btn_siguiente = ttk.Button(self.frm_supervision, text="Finalizar conteo", command=lambda:self.finalizar_conteo())
        btn_siguiente.grid(row=2, column=2, padx=5, pady=5)

    def iniciar_video(self) -> None:
        """
            Función encargada de inicializar el capturador de vídeo y evitar que se vuelva
            a inicializar cuando ya está activo.
        """
    
        global cap

        # Para evitar que se vuelva a iniciar el video
        self.btn_iniciar.config(state=DISABLED)
        self.btn_regresar.config(state=DISABLED)
        cap = cv.VideoCapture(0)
        self.visualizar()

    def visualizar(self) -> None:
        """
            Función encargada de mostrar los marcos del vídeo en la GUI, además de
            cargar el modelo para reconocer y seguir las piezas de pan.
        """

        global cap

        if cap is not None:
            ret, frame = cap.read()
            if ret == True:
                blob = cv.dnn.blobFromImage(frame, scalefactor=1/255, size=(640,640), mean=[0,0,0], swapRB=True, crop=False)
                self.red.setInput(blob)
                detecciones = self.red.forward()[0]

                ids_clases = []
                confianzas = []
                cajas = []
                filas = detecciones.shape[0]

                marco_ancho, marco_alto = frame.shape[1], frame.shape[0]
                escala_x = marco_ancho/640
                escala_y = marco_alto/640

                for i in range(filas):
                    fila = detecciones[i]
                    confianza = fila[4]
                    if confianza > 0.5:
                        puntaje_clases = fila[5:]
                        indice = np.argmax(puntaje_clases)
                        if puntaje_clases[indice] > 0.5:
                            cx, cy, w, h = fila[:4]
                            x1 = int((cx-w/2)*escala_x)
                            y1 = int((cy-h/2)*escala_y)
                            ancho = int(w*escala_x)
                            alto = int(h*escala_y)

                            # Solo si se encuentra dentro del marco dibujado es contado
                            if 160 <= x1 <= 480:
                                ids_clases.append(indice)
                                confianzas.append(confianza)
                                caja = np.array([x1, y1, ancho, alto])
                                cajas.append(caja)
                
                indices = cv.dnn.NMSBoxes(cajas,confianzas,0.5,0.5)

                # Alerta de que no se ha detectado una nueva pieza de pan
                if len(indices) == 0:
                    self.contador_retraso += 1
                else:
                    self.contador_retraso = 0

                if self.contador_retraso == 120:
                    self.contador_retraso = 0
                    messagebox.showwarning('Conteo', 'No se detectó pan, por lo tanto termino la operación.')
                    self.finalizar_conteo()
                
                # Dibujando el marco donde se puede hacer la detección
                line_x = 320 // 2
                line_y = 480
                cv.line(frame, (line_x, 0), (line_x, 480), (0, 0, 255), 2)
                cv.line(frame, (line_y, 0), (line_y, 480), (0, 0, 255), 2)

                for i in indices:
                    x1, y1, w, h = cajas[i]
                    etiqueta = self.clases[ids_clases[i]]
                    conf = confianzas[i]
                    texto = etiqueta + "{:.2f}".format(conf)

                    if self.bbox is None:
                        self.bbox = (x1, y1, w, h)
                        ok = self.tracker.init(frame, self.bbox)

                        # Contando solo el pan que se eligió
                        if self.rd_elegido.get() == etiqueta:
                            self.conteo += 1
                    else:
                        ok, self.bbox = self.tracker.update(frame)
                        if not ok:
                            self.bbox = None
                            self.tracker = cv.TrackerKCF_create()

                    if self.bbox is not None:
                        (x, y, w, h) = [int(v) for v in self.bbox]
                        cv.rectangle(frame,(x,y),(x+w,y+h),(255,0,0),2)
                        cv.putText(frame, texto,(x1,y1-2),cv.FONT_HERSHEY_COMPLEX,0.7,(255,0,255),2)

                cv.putText(frame, "Conteo: {}".format(self.conteo), (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                frame = imutils.resize(frame, width=480)
                frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)

                im = Image.fromarray(frame)
                img = ImageTk.PhotoImage(image=im)

                self.l_video.configure(image=img)
                self.l_video.image = img
                self.l_video.after(10, self.visualizar)
            else:
                self.l_video.image = ""
                cap.release()

    def finalizar_conteo(self) -> None:
        """
            Función encargada de detener el conteo y asignar un tiempo de fin de la operación.
        """

        global cap

        try:
            cap.release()

            ahora = datetime.now()
            self.hora_termino = ahora.strftime("%H:%M:%S")

            self.resumen_operacion()
        except:
            messagebox.showerror('Error', 'No ha generado un conteo.')

    def resumen_operacion(self) -> None:
        """
            Interfaz que muestra todos los datos asignados durante la operación.
        """

        self.raiz.geometry('450x425')

        self.frm_resumen.pack()
        self.frm_supervision.pack_forget()

        for widget in self.frm_resumen.winfo_children():
            widget.destroy()

        l_resumen = ttk.Label(self.frm_resumen, text='Resumen de la operación')
        l_resumen.config(font=('Helvatical bold',20))
        l_resumen.grid(row=0, column=0, padx=5, pady=10, columnspan=2)
        l_pza = ttk.Label(self.frm_resumen, text=f'Pieza de pan: {self.rd_elegido.get()}', font=5)
        l_pza.grid(row=1, column=0, sticky='w', padx=5, pady=5, columnspan=2)
        l_usr = ttk.Label(self.frm_resumen, text=f'Usuario operador: {self.usuario_operador}', font=5)
        l_usr.grid(row=2, column=0, sticky='w', padx=5, pady=5, columnspan=2)
        l_desc = ttk.Label(self.frm_resumen, text=f'Descripción:', font=5, width=40)
        l_desc.grid(row=3, column=0, sticky="w", padx=5, pady=5, columnspan=2)

        t_descripcion = Text(self.frm_resumen, width=40, height=5, bg="#F0F0F0", font=5)
        t_descripcion.grid(row=4, column=0, padx=5, pady=5, columnspan=2)
        t_descripcion.insert(INSERT, self.descripcion)
        t_descripcion.config(state=DISABLED)

        l_fecha = ttk.Label(self.frm_resumen, text=f'Fecha de operación: {self.fecha}', font=5)
        l_fecha.grid(row=5, column=0, sticky="w", padx=5, pady=5, columnspan=2)
        l_h_inicio = ttk.Label(self.frm_resumen, text=f'Hora de inicio: {self.hora_inicio}', font=5)
        l_h_inicio.grid(row=6, column=0, sticky="w", padx=5, pady=5, columnspan=2)
        l_h_fin = ttk.Label(self.frm_resumen, text=f'Hora de termino: {self.hora_termino}', font=5)
        l_h_fin.grid(row=7, column=0, sticky="w", padx=5, pady=5, columnspan=2)
        l_conteo = ttk.Label(self.frm_resumen, text=f'Piezas capturadas: {self.conteo}', font=5)
        l_conteo.grid(row=8, column=0, sticky="w", padx=5, pady=5, columnspan=2)

        btn_confirmar = ttk.Button(self.frm_resumen, text='Confirmar datos', command=lambda:self.subir_datos())
        btn_confirmar.grid(row=9, column=0, padx=5, pady=5)
        btn_descartar = ttk.Button(self.frm_resumen, text='Descartar datos', command=lambda:self.descartar_datos())
        btn_descartar.grid(row=9, column=1, padx=5, pady=5)
    
    def subir_datos(self) -> None:
        """
            Función encargada de almacenar los datos recabados de la operación
            en la base de datos.
        """

        respuesta = messagebox.askyesno('Confirmación', '¿Está seguro de subir la información recabada?')

        if respuesta:
            parametros = (
                self.rd_elegido.get(), 
                self.conteo, 
                self.hora_inicio, 
                self.hora_termino, 
                self.fecha, 
                self.descripcion, 
                self.id_usuario)
            operacion = ("INSERT INTO conteos "
                 "(nombre, cantidad, hora_inicio, hora_fin, fecha, descripcion, id_usuario) "
                 "VALUES (%s, %s, %s, %s, %s, %s, %s)")

            try:
                cnx = mysql.connector.connect(
                    user='root',
                    password='root',
                    host='localhost',
                    database='tt_prueba1'
                )
                cursor = cnx.cursor()
                cursor.execute(operacion, parametros)
                cnx.commit()
                messagebox.showinfo('BD', "Se insertó el registro de conteo.")
            except mysql.connector.Error as err:
                messagebox.showerror('BD', "No se insertó el registro de conteo.")
                print(err)
            finally:
                cursor.close()
                cnx.close()
                self.resetear_datos()

    def descartar_datos(self) -> None:
        """
            Función encargada de descartar los datos recabados de la operación.
        """

        respuesta = messagebox.askyesno(
            'Confirmación', 
            '¿Está seguro de descartar la información recabada? Si hace esto, no podrá recuperarla.')

        if respuesta:
            self.resetear_datos()

    def resetear_datos(self) -> None:
        """
            Función encargada de volver a la ventana de menú cuando se haya terminado una
            operación, además asigna un estado incial al capturador de vídeo y al contador
            de piezas de pan.
        """

        global cap

        cap = None
        self.conteo = 0
        self.ventana_seleccion()

if __name__=="__main__":
    raiz = Tk()
    Main(raiz)
    raiz.mainloop()
