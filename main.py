import os
import re
import shutil
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.utils import platform
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.behaviors import ButtonBehavior
from kivy.properties import StringProperty, NumericProperty
from kivy.metrics import dp
from kivy.graphics import Color, Ellipse
from kivy.clock import Clock

DB_NAME = "radon_data.db"
IMG_FILTERS = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]

def get_data_dir():
    app = App.get_running_app()
    data_dir = app.user_data_dir if app else "."
    os.makedirs(data_dir, exist_ok=True)
    return data_dir

def get_db_path():
    return os.path.join(get_data_dir(), DB_NAME)

def init_db():
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS centros (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, zona TEXT, fecha_medicion TEXT, imagen_exterior_path TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS detectores (id INTEGER PRIMARY KEY AUTOINCREMENT, centro_id INTEGER NOT NULL, planta TEXT, sala TEXT, fecha TEXT, detector_codigo TEXT, plano_path TEXT, punto_x REAL, punto_y REAL, foto_situacion_path TEXT, foto_detector_path TEXT, fecha_creacion TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY CHECK (id = 1), tecnico TEXT)")
    cur.execute("INSERT OR IGNORE INTO settings (id, tecnico) VALUES (1, "")")
    conn.commit()
    conn.close()

def crear_centro(nombre):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("INSERT INTO centros (nombre, zona, fecha_medicion, imagen_exterior_path) VALUES (?, "", ?, NULL)", (nombre, datetime.now().strftime("%d/%m/%Y")))
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid

def fetch_centros():
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, zona, fecha_medicion, imagen_exterior_path FROM centros ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_centro(centro_id):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("SELECT id, nombre, zona, fecha_medicion, imagen_exterior_path FROM centros WHERE id=?", (centro_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_centro(centro_id, nombre, zona, fecha, imagen_exterior_path):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("UPDATE centros SET nombre=?, zona=?, fecha_medicion=?, imagen_exterior_path=? WHERE id=?", (nombre, zona, fecha, imagen_exterior_path, centro_id))
    conn.commit()
    conn.close()

def update_centro_imagen(centro_id, path):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("UPDATE centros SET imagen_exterior_path=? WHERE id=?", (path, centro_id))
    conn.commit()
    conn.close()

def insert_detector(data):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("INSERT INTO detectores (centro_id, planta, sala, fecha, detector_codigo, plano_path, punto_x, punto_y, foto_situacion_path, foto_detector_path, fecha_creacion) VALUES (?,?,?,?,?,?,?,?,?,?,?)", data)
    rowid = cur.lastrowid
    conn.commit()
    conn.close()
    return rowid

def update_detector(detector_id, data):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("UPDATE detectores SET centro_id=?, planta=?, sala=?, fecha=?, detector_codigo=?, plano_path=?, punto_x=?, punto_y=?, foto_situacion_path=?, foto_detector_path=?, fecha_creacion=? WHERE id=?", data + (detector_id,))
    conn.commit()
    conn.close()

def fetch_detectores(centro_id):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("SELECT id, centro_id, planta, sala, fecha, detector_codigo, plano_path, punto_x, punto_y, foto_situacion_path, foto_detector_path, fecha_creacion FROM detectores WHERE centro_id=? ORDER BY id ASC", (centro_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_detector(detector_id):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("SELECT id, centro_id, planta, sala, fecha, detector_codigo, plano_path, punto_x, punto_y, foto_situacion_path, foto_detector_path, fecha_creacion FROM detectores WHERE id=?", (detector_id,))
    row = cur.fetchone()
    conn.close()
    return row

def delete_detector(detector_id):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("DELETE FROM detectores WHERE id=?", (detector_id,))
    conn.commit()
    conn.close()

def get_setting_tecnico():
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("SELECT tecnico FROM settings WHERE id=1")
    row = cur.fetchone()
    conn.close()
    return row[0] if row else ""

def set_setting_tecnico(valor):
    conn = sqlite3.connect(get_db_path())
    cur = conn.cursor()
    cur.execute("UPDATE settings SET tecnico=? WHERE id=1", (valor,))
    conn.commit()
    conn.close()

def show_popup(titulo, mensaje):
    popup = Popup(title=titulo, content=Label(text=mensaje, halign="center"), size_hint=(0.85, 0.4))
    popup.open()
    return popup

def elegir_archivo(callback, titulo="Selecciona una imagen"):
    content = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(6))
    chooser = FileChooserIconView(filters=IMG_FILTERS, path=os.path.expanduser("~"))
    content.add_widget(chooser)
    botones = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
    content.add_widget(botones)
    popup = Popup(title=titulo, content=content, size_hint=(0.92, 0.92))
    def confirmar(*_a):
        if chooser.selection:
            popup.dismiss()
            callback(chooser.selection[0])
    def cancelar(*_a):
        popup.dismiss()
    btn_cancel = Button(text="Cancelar")
    btn_cancel.bind(on_release=cancelar)
    btn_ok = Button(text="Seleccionar")
    btn_ok.bind(on_release=confirmar)
    botones.add_widget(btn_cancel)
    botones.add_widget(btn_ok)
    popup.open()
    return popup

def tomar_foto_camara(callback):
    data_dir = get_data_dir()
    filename = os.path.join(data_dir, f"foto_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.jpg")
    def on_complete(path=None):
        path = path or filename
        if path and os.path.exists(path):
            callback(path)
        else:
            elegir_archivo(callback)
    try:
        from plyer import camera
        camera.take_picture(filename=filename, on_complete=on_complete)
    except Exception:
        elegir_archivo(callback)

def elegir_o_tomar_foto(callback, titulo="Anadir imagen"):
    content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
    content.add_widget(Label(text=titulo, size_hint_y=None, height=dp(30)))
    popup = Popup(title=titulo, content=content, size_hint=(0.8, 0.35))
    def usar_camara(*_a):
        popup.dismiss()
        tomar_foto_camara(callback)
    def usar_archivo(*_a):
        popup.dismiss()
        elegir_archivo(callback)
    btn_camara = Button(text="Tomar foto", size_hint_y=None, height=dp(46))
    btn_camara.bind(on_release=usar_camara)
    btn_archivo = Button(text="Elegir de galeria / archivo", size_hint_y=None, height=dp(46))
    btn_archivo.bind(on_release=usar_archivo)
    content.add_widget(btn_camara)
    content.add_widget(btn_archivo)
    popup.open()
    return popup

def copiar_a_datos(origen, prefijo):
    data_dir = get_data_dir()
    ext = os.path.splitext(origen)[1] or ".jpg"
    destino = os.path.join(data_dir, f"{prefijo}_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}{ext}")
    shutil.copy(origen, destino)
    return destino

def _slug(texto):
    texto = (texto or "centro").lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
    return texto or "centro"

def abrir_ajustes_popup():
    content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
    content.add_widget(Label(text="Nombre del tecnico / empresa (aparecera en el PDF)", size_hint_y=None, height=dp(50)))
    input_tecnico = TextInput(text=get_setting_tecnico(), multiline=False, size_hint_y=None, height=dp(44))
    content.add_widget(input_tecnico)
    botones = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
    content.add_widget(botones)
    popup = Popup(title="Ajustes", content=content, size_hint=(0.85, 0.4))
    def guardar(*_a):
        set_setting_tecnico(input_tecnico.text.strip())
        popup.dismiss()
    btn_cerrar = Button(text="Cerrar")
    btn_cerrar.bind(on_release=lambda *_a: popup.dismiss())
    btn_guardar = Button(text="Guardar")
    btn_guardar.bind(on_release=guardar)
    botones.add_widget(btn_cerrar)
    botones.add_widget(btn_guardar)
    popup.open()
    return popup

def compartir_archivos(filepaths):
    filepaths = [f for f in filepaths if f and os.path.exists(f)]
    if not filepaths:
        show_popup("Error", "No hay archivos para compartir")
        return
    if platform != "android":
        rutas = "\n".join(filepaths)
        show_popup("Archivos generados", f"En un dispositivo Android podras compartir esto directamente por WhatsApp. Archivos listos en:\n{rutas}")
        return
    try:
        from plyer import share
    except Exception as exc:
        show_popup("Error al compartir", str(exc))
        return
    def compartir_siguiente(idx):
        if idx >= len(filepaths):
            return
        path = filepaths[idx]
        try:
            share.share(title="Compartir informe de radon", filepath=path)
        except Exception as exc:
            show_popup("Error al compartir", str(exc))
            return
        if idx + 1 < len(filepaths):
            Clock.schedule_once(lambda dt: compartir_siguiente(idx + 1), 1.5)
    compartir_siguiente(0)

class CentroCard(ButtonBehavior, BoxLayout):
    centro_id = NumericProperty(0)
    texto = StringProperty("")

class DetectorCard(ButtonBehavior, BoxLayout):
    detector_id = NumericProperty(0)
    texto = StringProperty("")

class PlanoMarcador(Widget):
    source = StringProperty("")
    norm_x = NumericProperty(-1)
    norm_y = NumericProperty(-1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.img = Image(allow_stretch=True, keep_ratio=True)
        self.add_widget(self.img)
        self.bind(size=self._reflow, pos=self._reflow)
        self.bind(source=self._on_source)
        self.bind(norm_x=self._reflow, norm_y=self._reflow)

    def _on_source(self, *_args):
        self.img.source = self.source
        self.img.reload()
        Clock.schedule_once(lambda dt: self._reflow(), 0)

    def _reflow(self, *_args):
        self.img.size = self.size
        self.img.pos = self.pos
        self._redraw_marker()

    def reset_marker(self):
        self.norm_x = -1
        self.norm_y = -1

    def _get_image_bounds(self):
        texture = self.img.texture
        if not texture:
            return None
        tex_w, tex_h = texture.size
        if not tex_w or not tex_h:
            return None
        widget_w, widget_h = self.size
        if not widget_w or not widget_h:
            return None
        img_ratio = tex_w / tex_h
        widget_ratio = widget_w / widget_h
        if img_ratio > widget_ratio:
            draw_w = widget_w
            draw_h = widget_w / img_ratio
        else:
            draw_h = widget_h
            draw_w = widget_h * img_ratio
        draw_x = self.x + (widget_w - draw_w) / 2
        draw_y = self.y + (widget_h - draw_h) / 2
        return draw_x, draw_y, draw_w, draw_h

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        bounds = self._get_image_bounds()
        if not bounds:
            return super().on_touch_down(touch)
        draw_x, draw_y, draw_w, draw_h = bounds
        if draw_x <= touch.x <= draw_x + draw_w and draw_y <= touch.y <= draw_y + draw_h:
            self.norm_x = (touch.x - draw_x) / draw_w
            self.norm_y = 1 - (touch.y - draw_y) / draw_h
            return True
        return super().on_touch_down(touch)

    def marcar_en(self, norm_x, norm_y):
        self.norm_x = norm_x
        self.norm_y = norm_y

    def _redraw_marker(self):
        self.canvas.after.clear()
        if self.norm_x < 0 or self.norm_y < 0:
            return
        bounds = self._get_image_bounds()
        if not bounds:
            return
        draw_x, draw_y, draw_w, draw_h = bounds
        px = draw_x + self.norm_x * draw_w
        py = draw_y + (1 - self.norm_y) * draw_h
        radius = dp(9)
        with self.canvas.after:
            Color(0.85, 0.1, 0.1, 1)
            Ellipse(pos=(px - radius, py - radius), size=(radius * 2, radius * 2))

class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._centros_por_nombre = {}

    def on_enter(self):
        Clock.schedule_once(lambda dt: self._cargar())

    def _cargar(self):
        centros = fetch_centros()
        self._centros_por_nombre = {}
        nombres = []
        for c in centros:
            cid, nombre, zona, fecha, img = c
            etiqueta = nombre or f"Centro {cid}"
            if etiqueta in self._centros_por_nombre:
                etiqueta = f"{etiqueta} ({cid})"
            self._centros_por_nombre[etiqueta] = cid
            nombres.append(etiqueta)
        self.ids.centro_spinner.values = nombres
        if nombres:
            if self.ids.centro_spinner.text not in nombres:
                self.ids.centro_spinner.text = nombres[0]
        else:
            self.ids.centro_spinner.text = "Selecciona un centro"
        container = self.ids.centros_container
        container.clear_widgets()
        if not centros:
            container.add_widget(Label(text="Todavia no hay centros registrados.", size_hint_y=None, height=dp(40), color=(0.4, 0.4, 0.4, 1)))
            return
        for c in centros:
            cid, nombre, zona, fecha, img = c
            texto = f"[b]{nombre or "Centro sin nombre"}[/b]\n{zona or "Sin zona"}    {fecha or ""}"
            card = CentroCard(centro_id=cid, texto=texto)
            card.bind(on_release=lambda inst, cid=cid: self._abrir(cid))
            container.add_widget(card)

    def _abrir(self, centro_id):
        app = App.get_running_app()
        centro_screen = app.root.get_screen("centro")
        centro_screen.abrir(centro_id)
        app.root.current = "centro"

    def abrir_centro_seleccionado(self):
        etiqueta = self.ids.centro_spinner.text
        cid = self._centros_por_nombre.get(etiqueta)
        if cid is None:
            show_popup("Selecciona un centro", "Elige un centro de la lista antes de abrirlo.")
            return
        self._abrir(cid)

    def crear_centro_popup(self):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        content.add_widget(Label(text="Nombre del nuevo centro", size_hint_y=None, height=dp(28)))
        input_nombre = TextInput(multiline=False, size_hint_y=None, height=dp(44))
        content.add_widget(input_nombre)
        botones = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        content.add_widget(botones)
        popup = Popup(title="Crear nuevo centro", content=content, size_hint=(0.85, 0.4))
        def crear(*_a):
            nombre = input_nombre.text.strip() or "Centro sin nombre"
            cid = crear_centro(nombre)
            popup.dismiss()
            self._abrir(cid)
        btn_cancel = Button(text="Cancelar")
        btn_cancel.bind(on_release=lambda *_a: popup.dismiss())
        btn_crear = Button(text="Crear")
        btn_crear.bind(on_release=crear)
        botones.add_widget(btn_cancel)
        botones.add_widget(btn_crear)
        popup.open()

    def abrir_ajustes(self):
        abrir_ajustes_popup()

class CentroScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.centro_id = None
        self._imagen_exterior_path = None
        self.modo_edicion = False
        self._fotos_checks = {}

    def abrir(self, centro_id):
        self.centro_id = centro_id
        self.modo_edicion = False
        Clock.schedule_once(lambda dt: self._cargar())

    def _cargar(self):
        centro = get_centro(self.centro_id)
        if not centro:
            return
        _, nombre, zona, fecha, img = centro
        self.ids.centro_titulo.text = nombre or "Centro"
        self.ids.centro_subtitulo.text = zona or "Sin zona"
        self.ids.nombre_input.text = nombre or ""
        self.ids.zona_input.text = zona or ""
        self.ids.fecha_medicion_input.text = fecha or ""
        self._imagen_exterior_path = img
        self.ids.imagen_exterior_preview.source = img or ""
        self.ids.editar_detectores_btn.text = "Ocultar edicion" if self.modo_edicion else "Editar detectores"
        self._cargar_detectores()

    def guardar_cambios_centro(self):
        nombre = self.ids.nombre_input.text.strip() or "Centro sin nombre"
        zona = self.ids.zona_input.text.strip()
        fecha = self.ids.fecha_medicion_input.text.strip()
        update_centro(self.centro_id, nombre, zona, fecha, self._imagen_exterior_path)
        self.ids.centro_titulo.text = nombre
        self.ids.centro_subtitulo.text = zona or "Sin zona"
        show_popup("Guardado", "Los datos del centro se han guardado.")

    def adjuntar_imagen_exterior(self):
        def al_elegir(path):
            destino = copiar_a_datos(path, "centro_exterior")
            self._imagen_exterior_path = destino
            self.ids.imagen_exterior_preview.source = destino
            self.ids.imagen_exterior_preview.reload()
            update_centro_imagen(self.centro_id, destino)
        elegir_o_tomar_foto(al_elegir, titulo="Imagen exterior del centro")

    def colocar_nuevo_detector(self):
        app = App.get_running_app()
        detector_screen = app.root.get_screen("detector")
        detector_screen.abrir(centro_id=self.centro_id, detector_id=None)
        app.root.current = "detector"

    def toggle_modo_edicion(self):
        self.modo_edicion = not self.modo_edicion
        self.ids.editar_detectores_btn.text = "Ocultar edicion" if self.modo_edicion else "Editar detectores"
        self._cargar_detectores()

    def _cargar_detectores(self):
        container = self.ids.detectores_container
        container.clear_widgets()
        detectores = fetch_detectores(self.centro_id)
        if not detectores:
            container.add_widget(Label(text="Todavia no hay detectores colocados.", size_hint_y=None, height=dp(36), color=(0.4, 0.4, 0.4, 1)))
        for d in detectores:
            (did, _centro_id, planta, sala, fecha, codigo, plano_path, px, py, foto_sit, foto_det, fecha_creacion) = d
            texto = f"[b]{sala or "Sala sin nombre"}[/b]\nPlanta {planta or "-"} . Cod. {codigo or "-"}"
            fila = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(64), spacing=dp(6))
            card = DetectorCard(detector_id=did, texto=texto)
            card.bind(on_release=lambda inst, did=did: self._editar_detector(did))
            fila.add_widget(card)
            if self.modo_edicion:
                btn_borrar = Button(text="Borrar", size_hint_x=None, width=dp(80), background_color=(0.8, 0.25, 0.25, 1))
                btn_borrar.bind(on_release=lambda inst, did=did: self._borrar_detector(did))
                fila.add_widget(btn_borrar)
            container.add_widget(fila)
        self._cargar_lista_fotos(detectores)

    def _editar_detector(self, detector_id):
        app = App.get_running_app()
        detector_screen = app.root.get_screen("detector")
        detector_screen.abrir(centro_id=self.centro_id, detector_id=detector_id)
        app.root.current = "detector"

    def _borrar_detector(self, detector_id):
        delete_detector(detector_id)
        self._cargar_detectores()

    def _cargar_lista_fotos(self, detectores):
        container = self.ids.fotos_container
        container.clear_widgets()
        self._fotos_checks = {}
        centro = get_centro(self.centro_id)
        img_exterior = centro[4] if centro else None
        if img_exterior and os.path.exists(img_exterior):
            self._agregar_check_foto(container, "Exterior del centro", img_exterior)
        for d in detectores:
            (did, _centro_id, planta, sala, fecha, codigo, plano_path, px, py, foto_sit, foto_det, fecha_creacion) = d
            if foto_sit and os.path.exists(foto_sit):
                self._agregar_check_foto(container, f"Sala {sala or did}", foto_sit)
            if foto_det and os.path.exists(foto_det):
                self._agregar_check_foto(container, f"Detector {codigo or did}", foto_det)
            if plano_path and os.path.exists(plano_path):
                self._agregar_check_foto(container, f"Plano {sala or did}", plano_path)

    def _agregar_check_foto(self, container, etiqueta, path):
        fila = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(8))
        chk = CheckBox(size_hint_x=None, width=dp(36))
        fila.add_widget(chk)
        lbl = Label(text=etiqueta, halign="left", valign="middle", color=(0.1, 0.1, 0.1, 1))
        lbl.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        fila.add_widget(lbl)
        container.add_widget(fila)
        self._fotos_checks[chk] = path

    def seleccionar_todas_fotos(self):
        if not self._fotos_checks:
            return
        marcar = not all(chk.active for chk in self._fotos_checks)
        for chk in self._fotos_checks:
            chk.active = marcar

    def generar_pdf_y_compartir(self):
        if not fetch_detectores(self.centro_id):
            show_popup("Sin datos", "Este centro todavia no tiene detectores colocados.")
            return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import cm
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
            from reportlab.lib import colors
            from PIL import Image as PILImage, ImageDraw
            centro = get_centro(self.centro_id)
            nombre = centro[1] if centro else "centro"
            filename = f"informe_{_slug(nombre)}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"
            output_path = os.path.join(get_data_dir(), filename)
            styles = getSampleStyleSheet()
            detectores = fetch_detectores(self.centro_id)
            tecnico = get_setting_tecnico()
            doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
            story = []
            story.append(Paragraph("Informe de medicion de radon", styles["Title"]))
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(f"<b>Centro:</b> {centro[1] or "-"}", styles["Normal"]))
            if centro[2]:
                story.append(Paragraph(f"<b>Zona:</b> {centro[2]}", styles["Normal"]))
            story.append(Paragraph(f"<b>Fecha de la medicion:</b> {centro[3] or "-"}", styles["Normal"]))
            if tecnico:
                story.append(Paragraph(f"<b>Tecnico:</b> {tecnico}", styles["Normal"]))
            story.append(Paragraph(f"<b>Numero de detectores:</b> {len(detectores)}", styles["Normal"]))
            story.append(Spacer(1, 0.5*cm))
            if centro[4] and os.path.exists(centro[4]):
                from reportlab.platypus import Image as RLImage
                with PILImage.open(centro[4]) as im:
                    w, h = im.size
                ratio = min(14*cm/w, 9*cm/h)
                story.append(Paragraph("Imagen exterior del centro:", styles["Heading4"]))
                story.append(RLImage(centro[4], width=w*ratio, height=h*ratio))
                story.append(Spacer(1, 0.5*cm))
            for idx, d in enumerate(detectores, start=1):
                (did, _centro_id, planta, sala, fecha, codigo, plano_path, punto_x, punto_y, foto_sit, foto_det, fecha_creacion) = d
                story.append(PageBreak())
                story.append(Paragraph(f"Detector {idx}: {sala or "-"}", styles["Heading2"]))
                datos_tabla = [
                    ["Planta", planta or "-"],
                    ["Sala", sala or "-"],
                    ["Codigo de detector", codigo or "-"],
                    ["Fecha", fecha or "-"],
                ]
                tabla = Table(datos_tabla, colWidths=[5*cm, 10*cm])
                tabla.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.append(tabla)
                story.append(Spacer(1, 0.4*cm))
                if plano_path and os.path.exists(plano_path):
                    story.append(Paragraph("Plano con ubicacion marcada:", styles["Heading4"]))
                    try:
                        temp_dir = os.path.join(get_data_dir(), "_pdf_tmp")
                        os.makedirs(temp_dir, exist_ok=True)
                        marcado_path = os.path.join(temp_dir, f"plano_marcado_{idx}.jpg")
                        img = PILImage.open(plano_path).convert("RGB")
                        w, h = img.size
                        draw = ImageDraw.Draw(img)
                        if punto_x is not None and punto_y is not None and punto_x >= 0:
                            px, py = punto_x * w, punto_y * h
                            r = max(6, int(min(w, h) * 0.018))
                            draw.ellipse((px - r, py - r, px + r, py + r), fill=(214, 30, 30), outline=(110, 0, 0), width=max(1, r//4))
                        img.save(marcado_path, quality=90)
                        from reportlab.platypus import Image as RLImage
                        with PILImage.open(marcado_path) as im:
                            w2, h2 = im.size
                        ratio2 = min(16*cm/w2, 10*cm/h2)
                        story.append(RLImage(marcado_path, width=w2*ratio2, height=h2*ratio2))
                    except Exception as exc:
                        story.append(Paragraph(f"(No se pudo procesar el plano: {exc})", styles["Normal"]))
                    story.append(Spacer(1, 0.4*cm))
                if foto_sit and os.path.exists(foto_sit):
                    story.append(Paragraph("Foto de la situacion del detector:", styles["Heading4"]))
                    with PILImage.open(foto_sit) as im:
                        w, h = im.size
                    ratio = min(9*cm/w, 9*cm/h)
                    story.append(RLImage(foto_sit, width=w*ratio, height=h*ratio))
                    story.append(Spacer(1, 0.4*cm))
                if foto_det and os.path.exists(foto_det):
                    story.append(Paragraph("Foto del detector:", styles["Heading4"]))
                    with PILImage.open(foto_det) as im:
                        w, h = im.size
                    ratio = min(9*cm/w, 9*cm/h)
                    story.append(RLImage(foto_det, width=w*ratio, height=h*ratio))
            doc.build(story)
            temp_dir = os.path.join(get_data_dir(), "_pdf_tmp")
            shutil.rmtree(temp_dir, ignore_errors=True)
            show_popup("Exito", f"PDF generado: {filename}")
            fotos_seleccionadas = [path for chk, path in self._fotos_checks.items() if chk.active]
            compartir_archivos([output_path] + fotos_seleccionadas)
        except Exception as exc:
            show_popup("Error al generar PDF", str(exc))

    def volver(self):
        App.get_running_app().root.current = "home"

class DetectorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.centro_id = None
        self.detector_id = None
        self._plano_path = None
        self._foto_situacion_path = None
        self._foto_detector_path = None

    def abrir(self, centro_id, detector_id=None):
        self.centro_id = centro_id
        self.detector_id = detector_id
        Clock.schedule_once(lambda dt: self._cargar())

    def _cargar(self):
        centro = get_centro(self.centro_id)
        self.ids.detector_centro_label.text = centro[1] if centro else ""
        if self.detector_id:
            d = get_detector(self.detector_id)
            (did, _centro_id, planta, sala, fecha, codigo, plano_path, px, py, foto_sit, foto_det, fecha_creacion) = d
            self.ids.detector_titulo.text = "Editar detector"
            self.ids.planta_input.text = planta or ""
            self.ids.sala_input.text = sala or ""
            self.ids.fecha_input.text = fecha or ""
            self.ids.detector_input.text = codigo or ""
            self._plano_path = plano_path
            self.ids.plano_widget.source = plano_path or ""
            if plano_path and px is not None and py is not None and px >= 0:
                self.ids.plano_widget.marcar_en(px, py)
            else:
                self.ids.plano_widget.reset_marker()
            self._foto_situacion_path = foto_sit
            self.ids.foto_situacion_preview.source = foto_sit or ""
            self._foto_detector_path = foto_det
            self.ids.foto_detector_preview.source = foto_det or ""
        else:
            self.ids.detector_titulo.text = "Nuevo detector"
            self._plano_path = None
            self._foto_situacion_path = None
            self._foto_detector_path = None
            self.ids.planta_input.text = ""
            self.ids.sala_input.text = ""
            self.ids.fecha_input.text = centro[3] if centro else ""
            self.ids.detector_input.text = ""
            self.ids.plano_widget.source = ""
            self.ids.plano_widget.reset_marker()
            self.ids.foto_situacion_preview.source = ""
            self.ids.foto_detector_preview.source = ""

    def adjuntar_plano(self):
        def al_elegir(path):
            destino = copiar_a_datos(path, "plano")
            self._plano_path = destino
            self.ids.plano_widget.reset_marker()
            self.ids.plano_widget.source = destino
        elegir_o_tomar_foto(al_elegir, titulo="Plano de situacion del detector")

    def foto_situacion(self):
        def al_tomar(path):
            destino = copiar_a_datos(path, "foto_situacion")
            self._foto_situacion_path = destino
            self.ids.foto_situacion_preview.source = destino
            self.ids.foto_situacion_preview.reload()
        elegir_o_tomar_foto(al_tomar, titulo="Foto de la situacion del detector")

    def foto_detector(self):
        def al_tomar(path):
            destino = copiar_a_datos(path, "foto_detector")
            self._foto_detector_path = destino
            self.ids.foto_detector_preview.source = destino
            self.ids.foto_detector_preview.reload()
        elegir_o_tomar_foto(al_tomar, titulo="Foto del detector")

    def cancelar(self):
        app = App.get_running_app()
        app.root.get_screen("centro").abrir(self.centro_id)
        app.root.current = "centro"

    def guardar_y_salir(self):
        planta = self.ids.planta_input.text.strip()
        sala = self.ids.sala_input.text.strip()
        fecha = self.ids.fecha_input.text.strip()
        codigo = self.ids.detector_input.text.strip()
        if not sala:
            show_popup("Falta informacion", "Indica la sala de la medicion.")
            return
        if not codigo:
            show_popup("Falta informacion", "Indica el codigo del detector.")
            return
        if self._plano_path:
            punto_x = self.ids.plano_widget.norm_x
            punto_y = self.ids.plano_widget.norm_y
        else:
            punto_x, punto_y = -1, -1
        data = (self.centro_id, planta, sala, fecha, codigo, self._plano_path, punto_x, punto_y, self._foto_situacion_path, self._foto_detector_path, datetime.now().strftime("%Y-%m-%d %H:%M"))
        if self.detector_id:
            update_detector(self.detector_id, data)
        else:
            self.detector_id = insert_detector(data)
        app = App.get_running_app()
        app.root.get_screen("centro").abrir(self.centro_id)
        app.root.current = "centro"

class RadonApp(App):
    title = "Detectores Rn"
    def build(self):
        init_db()
        from kivy.lang import Builder
        return Builder.load_file("ui.kv")

if __name__ == "__main__":
    RadonApp().run()
