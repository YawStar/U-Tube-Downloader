import sys
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtNetwork import QLocalServer, QLocalSocket

class SingletonApplication(QApplication):
    """
    Application တစ်ခုတည်းသာ ဖွင့်ခွင့်ပေးပြီး ဒုတိယ instance ဖွင့်ပါက 
    မူလ Application ထံ activationRequested signal ပို့ပေးမည့် Class (PySide6)
    """
    activationRequested = Signal()

    def __init__(self, argv, app_id: str):
        super().__init__(argv)
        self.app_id = app_id
        self._is_primary = False
        self._server = None

        # ရှိနှင့်ပြီးသား Server (မူလ Instance) ကို ချိတ်ဆက်ကြည့်မည်
        socket = QLocalSocket()
        socket.connectToServer(self.app_id)

        if socket.waitForConnected(500):
            # တခြား Instance ပွင့်နေပြီးသားဖြစ်၍ မူလ Instance ဆီ Activation Message ပို့မည်
            socket.write(b"ACTIVATE")
            socket.waitForBytesWritten(1000)
            socket.disconnectFromServer()
            self._is_primary = False
        else:
            # ပထမဦးဆုံး ပွင့်သော Primary Instance
            self._is_primary = True
            self._start_server()

    def is_primary_instance(self) -> bool:
        """ Primary (ပထမ) Instance ဟုတ်/မဟုတ် စစ်ဆေးပေးသည် """
        return self._is_primary

    def _start_server(self):
        """ Primary Instance အတွက် Socket Server စတင်မည် """
        self._server = QLocalServer(self)
        # အရင် ပိတ်မသွားဘဲ ကျန်ခဲ့သော Server name/pipe ရှိပါက ရှင်းထုတ်မည်
        QLocalServer.removeServer(self.app_id)
        
        if self._server.listen(self.app_id):
            self._server.newConnection.connect(self._on_new_connection)

    def _on_new_connection(self):
        """ ဒုတိယ Instance ထံမှ ချိတ်ဆက်မှု ရောက်လာပါက လက်ခံမည် """
        client_socket = self._server.nextPendingConnection()
        if client_socket:
            client_socket.readyRead.connect(lambda: self._handle_message(client_socket))

    def _handle_message(self, socket: QLocalSocket):
        """ ရောက်လာသော Message အား စစ်ဆေး၍ Signal ထုတ်ပေးမည် """
        msg = socket.readAll().data().decode("utf-8")
        if msg == "ACTIVATE":
            self.activationRequested.emit()
        socket.disconnectFromServer()