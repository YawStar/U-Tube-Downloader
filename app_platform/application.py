import sys
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket

class SingletonApplication(QApplication):
    """
    Application တစ်ခုတည်းသာ ဖွင့်ခွင့်ပေးပြီး ဒုတိယ instance ဖွင့်တဲ့အခါ
    မူလ Application ဆီကို activationRequested signal ပို့ပေးမယ့် Class (PySide6)
    """
    activationRequested = Signal()

    def __init__(self, argv, app_id: str):
        super().__init__(argv)
        self.app_id = app_id
        self._is_primary = False
        self._server = None

        # ရှိပြီးသား Server (မူလ Instance) ကို ချိတ်ဆက်ကြည့်
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)

        if socket.waitForConnected(500):
            # တခြား Instance ပွင့်နေပြီးသားမို့ မူလ Instance ဆီ Activation Message ပို့မယ်
            socket.write(b"ACTIVATE")
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            self._is_primary = False
        else:
            # ပထမဦးဆုံး ဖွင့်တဲ့ Primary Instance
            self._is_primary = True
            self._start_server()

    def is_primary_instance(self) -> bool:
        """ Primary (ပထမ) Instance ဟုတ်/မဟုတ် စစ်ဆေး """
        return self._is_primary

    def _start_server(self):
        """ Primary Instance အတွက် Socket Server စတင် """
        self._server = QLocalServer(self)
        # အရင် ပိတ်မသွားဘဲ ကျန်ခဲ့သော Server name/pipe ရှိရင် ရှင်းထုတ်
        QLocalServer.removeServer(self.app_id)
        
        if self._server.listen(self.app_id):
            self._server.newConnection.connect(self._on_new_connection)

    def _on_new_connection(self):
        """ ဒုတိယ Instance ထံကနေ ချိတ်ဆက်မှု ရောက်လာရင် လက်ခံ """
        client_socket = self._server.nextPendingConnection()
        if client_socket:
            client_socket.readyRead.connect(lambda: self._handle_message(client_socket))

    def _handle_message(self, socket: QLocalSocket):
        """ ရောက်လာသော Message ကိုစစ်ဆေးပြီး Signal ထုတ်ပေး """
        msg = socket.readAll().data().decode("utf-8")
        if msg == "ACTIVATE":
            self.activationRequested.emit()
        socket.disconnectFromServer()