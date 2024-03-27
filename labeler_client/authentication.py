import asyncio
import json
import os
import subprocess
import sys
import time
import webbrowser

import pydash
import requests
import websockets
from websockets import exceptions as ws_exceptions

from labeler_client.constants import DNS_NAME
from labeler_client.helpers import get_request, post_request


class Authentication:
    def __init__(self, host=None, project="base", token=None, port=5000):
        if not pydash.is_empty(host) and pydash.is_empty(project):
            raise Exception("Project cannot be None or empty.")
        self.host = host
        self.token = token
        self.project = project
        self.process = None
        self.port = port
        self.stop = None
        if pydash.is_empty(host):
            self.project = "base"
        if not pydash.is_empty(project):
            self.project = project
        response = get_request(path=self.__get_path() + "?url_check=1", timeout=5)
        if response.status_code != 200:
            raise Exception(response.text)
        self.__WEB_PORT = 52235
        self.__SOCKET_PORT = 52236
        if pydash.is_empty(token):
            self.__start_servers()

    def __signin(self, username, password):
        return post_request(
            path=f"{self.__get_path()}/users/signin",
            json={
                "username": username,
                "password": password,
            },
        )

    def __start_servers(self):
        path = os.path.dirname(__file__)
        try:
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "http.server",
                    str(self.__WEB_PORT),
                    "-b",
                    "localhost",
                    "-d",
                    f"{path}/web/auth/out",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            time.sleep(2)
            webbrowser.open(f"http://localhost:{self.__WEB_PORT}")
            self.stop = asyncio.Future()

            async def handler(websocket):
                data = None
                while True:
                    try:
                        data = await websocket.recv()
                        json_data = json.loads(data)
                        username = pydash.objects.get(json_data, "username", "")
                        password = pydash.objects.get(json_data, "password", "")
                        action = pydash.objects.get(json_data, "action", None)
                        if pydash.is_equal(action, "signin"):
                            response = self.__signin(username, password)
                            if response.status_code == 200:
                                data = pydash.objects.get(
                                    response.json(), "token", None
                                )
                                await websocket.send(json.dumps("done"))
                            else:
                                data = None
                                await websocket.send(
                                    json.dumps({"error": response.text})
                                )
                        elif pydash.is_equal(action, "signup"):
                            response = post_request(
                                path=f"{self.__get_path()}/users/register",
                                json={
                                    "invitation_code": pydash.objects.get(
                                        json_data, "invitation_code", ""
                                    ),
                                    "username": username,
                                    "password": password,
                                },
                            )
                            if response.status_code == 200:
                                response = self.__signin(username, password)
                                if response.status_code == 200:
                                    data = pydash.objects.get(
                                        response.json(), "token", None
                                    )
                                    await websocket.send(json.dumps("done"))
                                else:
                                    data = None
                                    await websocket.send(
                                        json.dumps({"error": response.text})
                                    )
                            else:
                                data = None
                                await websocket.send(
                                    json.dumps(
                                        {"error": response.text, "type": "register"}
                                    )
                                )
                    except ws_exceptions.ConnectionClosedOK:
                        break
                    except ws_exceptions.ConnectionClosedError:
                        break
                    except Exception as ex:
                        await websocket.send(json.dumps({"error": str(ex)}))
                self.stop.set_result(data)

            async def main():
                async with websockets.serve(handler, "", self.__SOCKET_PORT):
                    self.__set_token(await self.stop)
                    self.process.terminate()

            asyncio.run(main())
        except OSError as ex:
            if not pydash.is_empty(self.process):
                self.process.terminate()
            raise Exception(ex)
        except KeyboardInterrupt as ex:
            self.stop.set_result(None)

    def reauthenticate(self):
        self.__start_servers()

    def get_token(self):
        """
        Get current access token
        """
        return str(self.token)

    def __get_path(self):
        # megagon load balancer
        dns_name = DNS_NAME
        if not pydash.is_empty(self.host):
            dns_name = self.host
        return f"{dns_name}:{self.port}/{self.project}/auth"

    def get_access_tokens(self, job=False):
        """
        List personal access tokens (or job tokens) created by you

        Parameters
        ----------
        job : bool
            if true, return job tokens only
        """
        payload = {"token": self.token, "job": job}
        response = get_request(f"{self.__get_path()}/tokens", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def create_access_token(
        self, note: str = "", expiration_duration: int = 14, job=False
    ):
        """
        Create new access tokens: 2 weeks or no expiration

        Parameters
        ----------
        note : str
        expiration_duration : int
            unit: days, default to 14 days. If 0, it has no expiration (expires after 100 years)
        job : bool
            if true, create 1 hour job access tokens with job role and user id with "job_" prefix
        """
        payload = {
            "token": self.token,
            "note": note,
            "expiration_duration": expiration_duration,
            "job": job,
        }
        response = requests.post(f"{self.__get_path()}/tokens", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def delete_access_tokens(self, ids: list = []):
        """
        Delete access tokens (non ID tokens) based on given list of IDs

        Parameters
        ----------
        ids : list
        """
        payload = {"token": self.token}
        payload.update({"ids": ids})
        response = requests.delete(f"{self.__get_path()}/tokens", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def __set_token(self, token):
        if token == "":
            token = None
        self.token = token

    def __del__(self):
        if not pydash.is_empty(self.process):
            self.process.terminate()
        if not pydash.is_empty(self.stop) and not self.stop.done():
            self.stop.set_result(None)
