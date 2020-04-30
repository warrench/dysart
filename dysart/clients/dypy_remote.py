# -* coding: utf-8 -*-

"""
This module provides a native Python client library for Dysart using a
remote-object protocol to access Feature methods.
"""

import requests


class RemoteProject:
    """A handle to a remote Dysart project
    """

    def __init__(self, name: str, hostname: str, port: int):
        self.name = name
        self.hostname = hostname
        self.port = port

    @property
    def url(self):
        return f"http://{self.hostname}:{self.port}/remote/"

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

    @property
    def url(self):
        return self.project.url + f"feature/{self.name}/"

    def __getattr__(self, method_name: str):
        return RemoteProcedureCall(method_name, feature=self)


class RemoteProcedureCall:

    def __init__(self, name: str, feature: RemoteFeature):
        self.name = name
        self.feature = feature
    
    @property
    def url(self):
        return self.feature.url + f"{self.name}/"

    def __call__(self, *args, **kwargs):
        response = requests.get(self.url, data=[args, kwargs])
        return RemoteProcedureCall.interp_response(response)

    @staticmethod
    def interp_response(response):
        return response

if __name__ == '__main__':
    proj = RemoteProject(name='equs_demo', hostname='localhost', port='8000')
