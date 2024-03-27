from labeler_client.helpers import get_request, post_request


class Schema:
    '''
    The Schema class is used to define the schema for labeling annotations.

    Attributes
    ----------
    __service : object
        Service object for the connected project.
    '''

    def __init__(self, service):
        self.__service = service

    def set_schemas(self, schemas=None):
        '''
        Sets the user-defined schema

        Parameters
        ----------
        schemas : dict  
            Schema of annotation task which defines a `label_schema` which is a list of Python dictionaries defining the `name` of the label, the `level` of the label and `options` which defines a list of valid label options

            Full Example:
            ```json
            --8<-- "docs/assets/code/set_schemas.json"
            ```


        Raises
        -------
        Exception 
            If response code is not successful

        Returns
        -------
        response : json
            A json of the response
        '''
        payload = self.__service.get_base_payload()
        payload['schemas'] = schemas
        path = self.__service.get_service_endpoint('set_schemas')
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def value(self, active=None):
        '''
        Get project schema
        Parameters
        ------
        active : bool
            If `True`, only retrieve the active(latest) schema;
            if `False`, retrieve all previous schema; if `None`, retrieve 
            full history.
        '''
        payload = self.__service.get_base_payload()
        payload['active'] = active
        path = self.__service.get_service_endpoint('get_schemas')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_active_schemas(self):
        '''
        Get the active schema for the project.
        '''
        return self.value(active=True)

    def get_history(self):
        '''
        Get the full history of project schema
        '''
        return self.value(active=False)