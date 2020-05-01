# -* coding: utf-8 -*-

"""
This module provides a native Python client library for Dysart using a
remote-object protocol to access Feature methods.
"""

import pickle

import requests


class RemoteProject:
    """A handle to a remote Dysart project
    """

    def __init__(self, name: str, hostname: str, port: int):
        self.name = name
        self.hostname = hostname
        self.port = port

    def __getattr__(self, feature_name: str):
        """

        Returns: a handle to a remote object representing

        """
        return RemoteFeature(feature_name, project=self)


class RemoteFeature:
    """A handle to a remote Dysart feature
    """

    def __init__(self, name: str, project: RemoteProject):
        self.name = name
        self.project = project

    def __getattr__(self, method_name: str):
        return RemoteProcedureCall(method_name, feature=self)


class RemoteProcedureCall:

    def __init__(self, name: str, feature: RemoteFeature):
        self.name = name
        self.feature = feature
    
    def __call__(self, *args, **kwargs):
        proj = self.feature.project
        url = f"http://{proj.hostname}:{proj.port}/remote/feature"
        data = {
            'project': proj.name,
            'feature': self.feature.name,
            'method': self.name,
            'args': args,
            'kwargs': kwargs
        }
        response = requests.post(url, json=data)
        return RemoteProcedureCall.interp_response(response)

    @staticmethod
    def interp_response(response):
        response.raise_for_status()
        return pickle.loads(response.content)

if __name__ == '__main__':
    proj = RemoteProject(name='equs_demo',
                         hostname='127.0.0.1',
                         port=8000)
