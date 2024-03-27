import pydash

from labeler_client.authentication import Authentication
from labeler_client.constants import DNS_NAME
from labeler_client.helpers import (
    delete_request,
    get_request,
    post_request,
    put_request,
)


class Admin:
    def __init__(self, host=None, project="base", token=None, port=5000, auth=None):
        if pydash.is_empty(project):
            raise Exception("Project cannot be None or empty.")
        if pydash.is_empty(token) and pydash.is_empty(auth):
            raise Exception("At least 1 authentication method is required.")
        self.project = project
        self.token = token
        self.port = port
        self.auth: Authentication = auth
        self.host = host
        response = get_request(path=self.__get_path() + "?url_check=1", timeout=5)
        if response.status_code != 200:
            raise Exception(response.text)

    def __get_token(self):
        """
        Get token. If authentication object is used to initialize
        the service object, retrieve corresponding user token.
        """
        try:
            if not pydash.is_empty(self.token):
                return self.token
            elif not pydash.is_empty(self.auth):
                return self.auth.get_token()
        except:
            pass
        return None

    def get_base_payload(self):
        """
        Get the base payload for any REST request which includes the authentication token.
        """
        return {"token": self.__get_token()}

    def __get_path(self):
        # megagon load balancer
        dns_name = DNS_NAME
        if not pydash.is_empty(self.host):
            dns_name = self.host
        return f"{dns_name}:{self.port}/{self.project}/auth"

    def get_invitations(self, active=None):
        """
        Get all invitations based on filter: active
        None: all invitations
        True: only active invitations
        False: only expired invitations

        Parameters
        ----------
        active : bool
            default to None
        """
        payload = self.get_base_payload()
        payload.update({"active": active})
        response = get_request(path=f"{self.__get_path()}/invitations", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_invitation_by_invitation_code(self, invitation_code=None):
        """
        Get invitation by invitation code

        Parameters
        ---------
        invitation_code : str
            default to None
        """
        payload = self.get_base_payload()
        response = get_request(
            path=f"{self.__get_path()}/invitations/{invitation_code}", json=payload
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def renew_invitation(self, id: str):
        """
        Renew an invitation by id

        Parameters
        ---------
        id : str
        """
        payload = self.get_base_payload()
        payload.update({"id": id})
        response = put_request(path=f"{self.__get_path()}/invitations", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def revoke_invitation(self, id: str):
        """
        Invalidate an invitation by id

        Parameters
        ---------
        id : str
        """
        payload = self.get_base_payload()
        payload.update({"id": id})
        response = delete_request(path=f"{self.__get_path()}/invitations", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def create_invitation(
        self, code: str = None, role_code: str = None, single_use: bool = True
    ):
        """
        Create invitation code for user account registration

        Parameters
        ----------
        code : str
            custom code
        role_code : str
            short code for roles
        single_use : bool
            default True. If true, invitation code can only be used once. otherwise, it can be used multiple times.
        """
        payload = self.get_base_payload()
        payload.update({"code": code, "role_code": role_code, "single_use": single_use})
        response = post_request(path=f"{self.__get_path()}/invitations", json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)
