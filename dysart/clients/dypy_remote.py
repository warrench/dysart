# -* coding: utf-8 -*-

"""
This module provides a native Python client library for Dysart using a
remote-object protocol to access Feature methods.
"""

import json
import numbers
import pickle
import random
from typing import *

import requests
import graphviz

# This intentionally-global variable controls how much stuff is printed
verbose = True


class Client:
    """
    """

    cheerful_messages = [
        "Happy measuring!",
        "Have a five-sigma day in lab!",
        "May all your results be statistically significant.",
        "I hope your data looks as good as you do today!",
    ]

    def __init__(self, hostname: str, port: int, verbose: bool = True):
        self.hostname = hostname
        self.port = port
        self.url = f"http://{hostname}:{port}"
        self.verbose = verbose

    def project(self, name: str, token: Optional[str] = None):

        url = self.url + '/project'
        data = {
            'project': name,
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        response_data = json.loads(response.content)
        proj = RemoteProject(self, name, token=token)
        for feature_name, methods in response_data['features'].items():
            feature = RemoteFeature(feature_name, proj)
            for method_name in methods:
                method = RemoteProcedureCall(method_name, feature)
                setattr(feature, method_name, method)
            setattr(proj, feature_name, feature)
        if verbose:
            print(f"Loaded project `{name}`.", random.choice(self.cheerful_messages))
            display_graph(response_data['graph'])
        return proj
    
    def debug(self):
        """Suspends execution of the server process and transfers control
        to a debugger. Invocation of this request should be forbidden by
        the server except with admin authentication

        Returns:

        """
        if verbose:
            print("Attempting to suspend execution... ")
        response = requests.post(self.url + '/debug')
        response.raise_for_status()
        if verbose:
            print("Resumed.")


class RemoteProject:
    """A handle to a remote Dysart project
    """

    def __init__(self, client: Client, name: str, token: Optional[str] = None):
        self.client = client
        self.name = name
        self.token = token

    def _repr_svg_(self):
        """Define this to get nice formatting in a Jupyter notebook
        
        Returns:

        """
        pass


class RemoteFeature:
    """A handle to a remote Dysart feature
    """

    def __init__(self, name: str, project: RemoteProject):
        self.name = name
        self.project = project
        self.url = '/'.join([self.project.client.url, 'feature'])

    def _repr_html_(self):
        data = {
            'project': self.project.name,
            'feature': self.name,
        }        
        response = requests.get(self.url, json=data)
        response.raise_for_status()
        return feature_html_table(json.loads(response.content))


class RemoteProcedureCall:

    def __init__(self, name: str, feature: RemoteFeature):
        self.name = name
        self.feature = feature
    
    def __call__(self, *args, **kwargs):
        proj = self.feature.project
        data = {
            'project': proj.name,
            'feature': self.feature.name,
            'method': self.name,
            'args': args,
            'kwargs': kwargs
        }
        if verbose:
            print("Issuing request... ")
        response = requests.post(self.feature.url, json=data)
        return RemoteProcedureCall.interp_response(response)

    @staticmethod
    def interp_response(response):
        response.raise_for_status()
        return pickle.loads(response.content)


def feature_html_table(repr: dict) -> str:
    """
    
    Args:
        repr: A dictionary representation of a Feature's state with keys
        `name`, `id`, and `results`.
        }

    Returns: An HTML string representing the state of the Feature.

    """
    html = []
    add = html.append
    
    def result_row(name: str, val: Any):
        if isinstance(val, numbers.Number):
            val_fmt = '{:.5e}'
        else:
            val_fmt = '{}'
        add(f"<tr><td>{name}</td><td>{val_fmt}</td></tr>".format(val))
    
    add(f"<h2>Feature <code>{repr['name']}</code></h2>")
    add(f"<h3>Id: <code>{repr['id']}</code></h3>")
    add("<table>")
    for name, val in repr['results'].items():
        result_row(name, val)
    add("</table>")
    return ''.join(html)


def display_graph(edges: List[Tuple[str, str]]):
    d = graphviz.Digraph()
    for edge in edges:
        d.edge(*edge)
    try:
        # This routine is defined if you're running inside a Jupyter notebook.
        # It comes from `IPython.core.display`, but I'm not really sure how
        # it works.
        display(d)
    except NameError:
        # You aren't in a Jupyter notebook, I guess
        pass

class Shout(object):
    def __init__(self, text):
        self.text = text

    def _repr_html_(self):
        return "<h1>" + self.text + "</h1>"

if __name__ == '__main__':
    proj = RemoteProject(name='equs_demo',
                         hostname='127.0.0.1',
                         port=8000)
