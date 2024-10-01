from textual import work, events, on
from textual.app import App, ComposeResult
from textual.containers import (
    Vertical,
    Container,
    Horizontal,
    VerticalScroll,
)
from textual.widgets import (
    Input,
    Markdown,
    Button,
    Header,
    Footer,
    Label,
    Log,
    Select,
)
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from py122u import nfc
import time
from textual.worker import Worker, WorkerState
from threading import Thread
import http.client
import json
import re


SERVER_ADDRESS = 'kind-hermit-freely.ngrok-free.app'
TEAM_OPTIONS = [
    ("Z.N.E", "Z.N.E"),
    ("Forum", "Forum"),
    ("Ultraboost", "Ultraboost"),
    ("Samba", "Samba"),
    ("Gazelle", "Gazelle"),
    ("Superstar", "Superstar"),
    ("Stan Smith", "Stan Smith"),
    ("Campus", "Campus"),
    ("Copa", "Copa"),
    ("Adilette", "Adilette"),
    ("Ozweego", "Ozweego"),
    ("Centenial", "Centenial"),
    ("Orketro", "Orketro"),
    ("Supernova", "Supernova"),
    ("Predator", "Predator"),
]

class MainScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container(classes="body"):
            with Vertical(classes="titleContainer"):
                yield Label("Registro de Usuarios", classes="h1")
            
            with Vertical(classes="formField"):
                yield Label("Seleccione un equipo")
                yield Select(TEAM_OPTIONS, id="teamSelction")
            
            with Vertical(classes="formField"):
                yield Label("Manilla")
                with Horizontal(id="nfcIdInput"):
                    yield Input("", id="nfc_id")
                    yield Button("Leer", id="leerncfc")
            
            with Vertical(classes="formField"):
                yield Label("Nombre")
                yield Input("", id="nombre")
            
            with Vertical(classes="formField"):
                yield Button("Registrar", id="registrar", classes="fullWidthBtn")

            yield Log(id="logger")
            
            with Vertical(classes="formField"):
                yield Button("Limpiar consola", id="clearConsole", classes="fullWidthBtn")

        yield Footer()

    #leer ususario
    @on(Button.Pressed, "#leer")
    def action_get_data(self):
        try:
            nfc_id = self.query_one("#nfc_id", Input).value
            if  nfc_id == "":
                self.query_one("#logger", Log).write_line(
                    "Por favor, acerque la manilla de nuevo "
                )
                return


            self.run_worker(self.add_user(nfc_id), exclusive=True)

            self.query_one("#logger", Log).clear()
            self.query_one("#logger", Log).write_line("Lectura completada")

        except Exception as e:
            print(e)
    
    #registrar usuario
    @on(Button.Pressed, "#registrar")
    def action_registrar(self):
        try:
            nfc_id = self.query_one("#nfc_id", Input).value
            name = self.query_one("#nombre", Input).value
            team = self.query_one("#teamSelction", Select).value
            
            if name == "" or team == "" or nfc_id == "":
                self.query_one("#logger", Log).write_line("Por favor, complete todos los campos")
                return

            self.run_worker(self.add_user(name, team, nfc_id), exclusive=True)

            self.query_one("#nfc_id", Input).value = ""
            self.query_one("#nombre", Input).value = ""
            self.query_one("#teamSelction", Input).value = ""
            self.query_one("#nfc_id", Input).classes = ""
            self.query_one("#logger", Log).clear()
            self.query_one("#logger", Log).write_line("Usuario Registrado con éxito")

        except Exception as e:
            print(e)

    async def add_user(self, name, team, nfc_id) -> None:
        conn = http.client.HTTPSConnection(SERVER_ADDRESS)
        payload = json.dumps({"name": name, "team": team, "id": nfc_id, "score": 0})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/signup", payload, headers) #Definir APi que envia los valores 
        res = conn.getresponse()
        data = res.read()

        self.query_one("#logger", Log).write_line(data.decode("utf-8"))
        print(data.decode("utf-8"))

    #leer nfc
    @on(Button.Pressed, "#leerncfc")
    def action_leerNFC(self):
        self.query_one("#logger", Log).clear()
        try:

            reader = nfc.Reader()
            reader.connect()  #conecata al lector NFC
            list = reader.get_uid()  #Recupera el identificador unico de la tarjeta en bites 
            guid = ""
            for i in list:
                guid += str(i) # transfomra cada NFC card' ID en String stored in GUID 
            self.query_one("#nfc_id", Input).value = guid # displays el valor de GUID  en la UI
            # 1. Guardar el GUID en un objeto donde podemos guardar el nombre y el correo de la persona en la base de datos.
            # 2. aca podesmo hacer un llamada al Back end para guardar el valor GUID de la tarjeta.
            # 3  ....
            self.query_one("#nfc_id", Input).classes = "success"  # cambia la clase del elemento para que si la operacion es exitosa se ilumine verde
        except Exception as e:
            self.query_one("#logger", Log).write_line("Coloque la tarjeta nuevamente")
            
    #limpiar consola
    @on(Button.Pressed, "#clearConsole")
    def action_clearConsole(self):
        self.query_one("#logger", Log).clear()


class ScoreManagementScreen(Screen):
    def compose(self) -> ComposeResult:
        yield Header()

        with VerticalScroll(classes="body"):
            with Vertical(classes="titleContainer"):
                yield Label("Consulta de Puntaje", classes="h1")
            
            with Vertical(classes="formField"):
                yield Label("Id NFC")
                with Horizontal(id="nfcIdInput"):
                    yield Input("", id="nfc_id")
                    yield Button("Leer", id="leerncfc")
            
            with Vertical(classes="formField"):
                yield Button("Consular puntaje", id="consultar", classes="fullWidthBtn")
            
            with Vertical(classes="formField"):
                yield Label("Puntuacion Actual")
                yield Input("", id="puntaje")

            with Vertical(classes="titleContainer"):
                yield Label("Ingrese el puntaje y elija una operación ↓", classes="h1")

            with Vertical(classes="formField"):
                yield Label("Modificar puntos")
                yield Input("", id="new_score")

            with Horizontal(id="scoreActionsContainer"):
                yield Button("Agregar", classes="score_button", id="add")
                yield Button("Restar", classes="score_button", id="deduct")
                yield Button("Asignar", classes="score_button", id="set")

            yield Log(id="logger")
            
            with Vertical(classes="formField"):
                yield Button("Limpiar consola", id="clearConsole", classes="fullWidthBtn")
        yield Footer()

    #leer puntaje de un usuario con nfc 
    async def get_score(self, nfc_id) -> None: 
        conn = http.client.HTTPSConnection(SERVER_ADDRESS)  
        endPoint = f"/get-user-score/{nfc_id}"
        conn.request("GET", endPoint) 
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        score = str(json_data['score'])
        self.query_one("#puntaje", Input).value = score
    

    # event consultar
    @on(Button.Pressed, "#consultar")
    def action_consultar(self):
        try:
            nfcId = self.query_one("#nfc_id", Input).value
            
            if nfcId == "":
                self.query_one("#logger", Log).write_line("Ingrese un ID para consultar")
                return
            
            self.run_worker(self.get_score(nfcId),exclusive=True)
        except Exception as e:
            print(e)
    
    #add score
    async def add_score(self, nfc_id, puntaje) -> None:
        conn = http.client.HTTPSConnection(SERVER_ADDRESS)
        payload = json.dumps({"id": nfc_id, "increment": puntaje})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/add-score", payload, headers) 
        res = conn.getresponse()
        data = res.read()

        self.query_one("#logger", Log).write_line(data.decode("utf-8")) 
        print(data.decode("utf-8"))

    #deduct score
    async def deduct_score(self, nfc_id, puntaje) -> None:
        conn = http.client.HTTPSConnection(SERVER_ADDRESS)
        payload = json.dumps({"id": nfc_id, "decrement": puntaje})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/subtract-score", payload, headers)
        res = conn.getresponse()
        data = res.read()

        self.query_one("#logger", Log).write_line(data.decode("utf-8")) 
        print(data.decode("utf-8"))

    #set score
    async def set_score(self, nfc_id, puntaje) -> None:
        conn = http.client.HTTPSConnection(SERVER_ADDRESS)
        payload = json.dumps({"id": nfc_id, "newScore": puntaje})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/set-score", payload, headers) 
        res = conn.getresponse()
        data = res.read()

        self.query_one("#logger", Log).write_line(data.decode("utf-8")) 
        print(data.decode("utf-8"))
    
    #Score button event
    @on(Button.Pressed, ".score_button")
    def action_score(self, event: Button.Pressed):
        try:
            nfcId = self.query_one("#nfc_id", Input).value
            score = self.query_one("#new_score", Input).value
            button_label = event.button._id
            
            if score == "" or nfcId == "":
                self.query_one("#logger", Log).write_line("Por favor, complete todos los campos.")
                return
            
            if button_label == "add":
                self.run_worker(self.add_score(nfcId, score), exclusive=True)
                return
            elif button_label == "deduct":
                self.run_worker(self.deduct_score(nfcId, score), exclusive=True)
                return
            elif button_label == "set":
                self.run_worker(self.set_score(nfcId, score), exclusive=True)
                return

        except Exception as e:
            print(e)

    #leer nfc
    @on(Button.Pressed, "#leerncfc")
    def action_leerNFC(self):
        self.query_one("#logger", Log).clear()
        try:

            reader = nfc.Reader()
            reader.connect()
            list = reader.get_uid()
            guid = ""
            for i in list:
                guid += str(i)
            self.query_one("#nfc_id", Input).value = guid
            self.query_one("#nfc_id", Input).classes = "success" 
        except Exception as e:
            self.query_one("#logger", Log).write_line("Coloque la tarjeta nuevamente")

    #limpiar consola
    @on(Button.Pressed, "#clearConsole")
    def action_clearConsole(self):
        self.query_one("#logger", Log).clear()

class NFCControllApp(App):
    
    CSS_PATH = "screen02.tcss"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True, priority=True),
        Binding("registro", "registro", "Registro", show=True, priority=True),
        Binding("Puntaje", "puntaje", "puntaje", show=True, priority=True),
    ]
    SCREENS = {"main": MainScreen, "score": ScoreManagementScreen}

    def on_mount(self) -> None:
        self.push_screen(MainScreen())

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_registro(self):
        self.push_screen(MainScreen())

    def action_puntaje(self):
        self.push_screen(ScoreManagementScreen())

if __name__ == "__main__":
    app = NFCControllApp()
    app.run()
