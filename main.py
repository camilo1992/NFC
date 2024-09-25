from textual import work, events, on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, Container, Horizontal
from textual.widgets import (
    Input,
    Markdown,
    Button,
    Header,
    Footer,
    Label,
    Rule,
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


class MainScreen(Screen):
    regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"

    def compose(self) -> ComposeResult:
        options = [
            ("Equipo 1", 1),
            ("Equipo 2", 2),
            ("Equipo 3", 3),
            ("Equipo 4", 4),
            ("Equipo 5", 5),
            ("Equipo 6", 6),
            ("Equipo 8", 8),
            ("Equipo 9", 9),
            ("Equipo 10", 10),
            ("Equipo 11", 11),
        ]
        
        with Container():
            yield Label("Seleccione un quipo") # ACA PODEMOS COLOCAR LOS EQUIPOS
            yield Select(options, id="teamSelction")
            
        with Container():
            yield Label("Manilla")
            with Horizontal():
                yield Input("", id="nfc_id")
                yield Button("Leer", id="leerncfc")
            
            yield Label("Nombre")
            yield Input("", id="nombre")
            yield Button("Registrar", id="registrar")
            yield Log(id="mensaje")

        yield Footer()

    #leer ususario
    @on(Button.Pressed, "#leer")
    def action_get_data(self):
        try:
            nfc_id = self.query_one("#nfc_id", Input).value
            if  nfc_id == "":
                self.query_one("#mensaje", Log).write_line(
                    "Por favor, acerque la manilla de nuevo "
                )
                return


            self.run_worker(self.add_user(nfc_id), exclusive=True)

            self.query_one("#mensaje", Log).clear()
            self.query_one("#mensaje", Log).write_line("Lectura completada")

        except Exception as e:
            print(e)
    
    @on(Button.Pressed, "#registrar")
    def action_registrar(self):
        try:
            nfc_id = self.query_one("#nfc_id", Input).value
            name = self.query_one("#nombre", Input).value
            team = self.query_one("#teamSelction", Select).value
            
            if name == "" or team == "" or nfc_id == "":
                self.query_one("#mensaje", Log).write_line("Por favor, complete todos los campos")
                return

            self.run_worker(self.add_user(name, team, nfc_id), exclusive=True)

            self.query_one("#nfc_id", Input).value = ""
            self.query_one("#nombre", Input).value = ""
            self.query_one("#teamSelction", Input).value = ""
            self.query_one("#nfc_id", Input).classes = ""
            self.query_one("#mensaje", Log).clear()
            self.query_one("#mensaje", Log).write_line("Usuario Registrado con éxito")

        except Exception as e:
            print(e)

    async def add_user(self, name, team, nfc_id) -> None:
        conn = http.client.HTTPSConnection("kind-hermit-freely.ngrok-free.app")
        payload = json.dumps({"name": name, "team": team, "id": nfc_id, "score": 0})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/signup", payload, headers) #Definir APi que envia los valores 
        res = conn.getresponse()
        data = res.read()

        self.query_one("#mensaje", Log).write_line(data.decode("utf-8"))
        print(data.decode("utf-8"))

    
    @on(Button.Pressed, "#leerncfc")
    def action_leerNFC(self):
        self.query_one("#mensaje", Log).clear()
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
            self.query_one("#nfc_id", Input).value = "Coloque la tarjeta nuevamente"
            self.query_one("#nfc_id", Input).classes = "error"
            print(e)


class NFCControllApp(App):
    CSS_PATH = "screen02.tcss"
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", show=True, priority=True),
        Binding("ctrl+q", "quit", "Quit", show=True, priority=True),
        Binding("registro", "registro", "Registro", show=True, priority=True),
        Binding("Leer puntaje", "acceso", "puntos", show=True, priority=True),
    ]
    SCREENS = {"main": MainScreen}

    def on_mount(self) -> None:
        print("Mounted")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()

    def action_registro(self):
        self.push_screen(MainScreen())

    def action_acceso(self):
        self.push_screen(AccesoScreen())


class AccesoScreen(Screen):
    active = False
    salon = 0

    def compose(self) -> ComposeResult:
        
        yield Header()
        with Container():
            yield Markdown("Leer Puntaje", id="titulo", classes="h1")
            yield Markdown("Por favor, acerque su tarjeta NFC al lector")
        
            yield Label("Manilla")        
            yield Input("", id="nfc_id")
            yield Button("Leer", id="leerncfc")
            
            yield Button("Consular puntaje", id="consultar")
            with Horizontal():
                 yield Label("Puntuacion")
                 yield Input("", id="puntaje")
            with Horizontal():
                 yield Button("Agregar", id="agregar")
                 yield Button("Restar", id="restar")
                 yield Button("Asignar", id="asignar")
            with Horizontal():
                 yield Label("Agregar puntos")
                 yield Input("0", id="Agregar_puntos")
            
            
            yield Log("", id="respuesta")

        yield Footer()


    #leer puntaje de un usuario con nfc 
    async def get_score(self, nfc_id) -> None: 
        conn = http.client.HTTPSConnection("kind-hermit-freely.ngrok-free.app")  
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
            
            self.run_worker(self.get_score(nfcId),exclusive=True)
        except Exception as e:
            print(e)
    
     #sumar puntaje
    async def add_score(self, nfc_id, puntaje) -> None:
        conn = http.client.HTTPSConnection("kind-hermit-freely.ngrok-free.app")
        payload = json.dumps({"id": nfc_id, "increment": puntaje})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/add-score", payload, headers) 
        res = conn.getresponse()
        data = res.read()

        self.query_one("#respuesta", Log).write_line(data.decode("utf-8")) 
        print(data.decode("utf-8"))

    @on(Button.Pressed, "#agregar")
    def action_agregar(self):
        try:
            nfcId = self.query_one("#nfc_id", Input).value
            puntajeExtra = self.query_one("#Agregar_puntos", Input).value
            self.run_worker(self.add_score( nfcId, puntajeExtra),exclusive=True)
        except Exception as e:
            print(e)

    
    #restar puntaje
    async def deduct_score(self, nfc_id, puntaje) -> None:
        conn = http.client.HTTPSConnection("kind-hermit-freely.ngrok-free.app")
        payload = json.dumps({"id": nfc_id, "decrement": puntaje})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/subtract-score", payload, headers)
        res = conn.getresponse()
        data = res.read()

        self.query_one("#respuesta", Log).write_line(data.decode("utf-8")) 
        print(data.decode("utf-8"))
    
    @on(Button.Pressed, "#restar")
    def action_agregar(self):
        try:
            nfcId = self.query_one("#nfc_id", Input).value
            puntajeExtra = self.query_one("#Agregar_puntos", Input).value
            self.run_worker(self.deduct_score( nfcId, puntajeExtra),exclusive=True)
        except Exception as e:
            print(e)

    
    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.salon = str(event.value)
        self.log(f"Equipo seleccionado: {self.salon}")
        self.query_one("#mensaje", Log).write_line(f"Equipo seleccionado: {self.salon}")

    @on(Button.Pressed, "#leernfc")
    async def action_leernfc(self):

        self.active = True
        self.read_nfc()

    @on(Button.Pressed, "#stopleernfc")
    async def action_stopleernfc(self):
        self.active = False

    @work(exclusive=True, thread=True)
    async def read_nfc(self) -> None:
        self.log("Leyendo tarjeta NFC")
        try:
            reader = nfc.Reader()
            reader.connect()
            list = reader.get_uid()
            guid = ""
            for i in list:
                guid += str(i)
            self.query_one("#nfc_id", Input).value = guid

            self.run_worker(self.checkin(),exclusive=True)
            time.sleep(5)
        except Exception as e:
            self.query_one("#nfc_id", Input).value = "Coloque una nueva tarjeta"
            time.sleep(0.5)

    async def on_worker_state_changed(self, event: Worker.StateChanged):

        if event.state == WorkerState.SUCCESS:

            if self.active:
                self.read_nfc()

    async def checkin(self):
        conn = http.client.HTTPSConnection("nfc.ekuulu.com")
        payload = json.dumps({"nfcid": self.query_one("#nfc_id", Input).value, "room": self.salon})
        headers = {"Content-Type": "application/json"}
        conn.request("POST", "/api/checkin", payload, headers)
        res = conn.getresponse()
        data = res.read()
        json_data = json.loads(data.decode("utf-8"))
        name = json_data["name"]
        self.query_one("#mensaje", Log).write_line(
                f"Acceso Registrado: {name} en el salón {self.salon}"
            )
    

    @on(Button.Pressed, "#ingresar")
    def action_ingresar(self):
        try:
            nfc_id = self.query_one("#nfc_id", Input).value
            if nfc_id == "":
                self.query_one("#mensaje", Log).write_line(
                    "Por favor, acerque su tarjeta NFC al lector"
                )
                return
            else:
                self.query_one("#nfc_id", Input).value = ""
                self.query_one("#nfc_id", Input).classes = ""
                self.query_one("#mensaje", Log).clear()
                self.query_one("#mensaje", Log).write_line("Acceso concedido")
        except Exception as e:
            print(e)

    @on(Button.Pressed, "#leerncfc")
    def action_leerNFC(self):
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
            self.query_one("#nfc_id", Input).value = "Coloque la tarjeta nuevamente"
            self.query_one("#nfc_id", Input).classes = "error"
            print(e)

    def action_ingresar(self):
        self.push_screen(MainScreen())


    


if __name__ == "__main__":
    app = NFCControllApp()
    app.run()
