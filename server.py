#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def check_unique_login(self, new_login :str):
        result : bool
        result = True
        for client in self.server.clients:
            if client.login == new_login:
                result = False
        return result

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                decoded_login = decoded.replace("login:", "").replace("\r\n", "")
                if self.check_unique_login(decoded_login):
                    self.login = decoded_login

                    self.transport.write(
                        f"Привет, {self.login}!\n".encode()
                    )
                    self.transport.writelines(self.server.messages)
                else:
                    self.login = None
                    self.transport.write("Данный логин уже используется. Придумайте новый логин\n".encode())
            else:
                self.transport.write("Неправильный логин\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}\n"
        self.server.messages.append(message.encode())
        if self.server.messages.__len__()>10:
            self.server.messages.pop(0)

        for user in self.server.clients:
            user.transport.write(message.encode())


class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
