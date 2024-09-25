  @on(Button.Pressed, "#restar")
    def action_agregar(self):
        try:
            nfcId = self.query_one("#nfc_id", Input).value
            puntajeExtra = self.query_one("#Agregar_puntos", Input).value
            self.run_worker(self.deduct_score( nfcId, puntajeExtra),exclusive=True)
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

