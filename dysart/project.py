from typing import Dict
import importlib.util
import os
import sys

from dysart.messages.errors import ValidationError

import mongoengine as me
import yaml


class Project:
    """A wrapper class that handles project configuration parsing and
    feature loading.
    """

    def __init__(self, project_path: str):
        self.path = project_path
        with open(os.path.expanduser(self.path), 'r') as f:
            try:
                proj_yaml = yaml.load(f, yaml.Loader)
            except FileNotFoundError:
                # TODO maybe handle the failure case more gracefully.
                # TODO reuse code from the messages module to print error messages consistently
                print("Error: failed to find Dysart project at", project_path)
                return

        self.modules = {}    # Feature modules that have been included
        self.features = {}   # Features that have been included

        # Next, import the libraries specified in the project specification
        for mod_path in proj_yaml['Modules']:
            self.load_feature_module(mod_path)

        # Finally, include the features.
        for feature_name, feature_meta in proj_yaml['Features'].items():
            # `feature_ident` is the feature identifier that will become its variable name
            # in the global scope. This is distinct from the `id` field within `feature_meta`,
            # which is used as a database index.
            # TODO
            # Check that the feature is defined correctly, and reject the load if there are errors.

            try:
                self.__validate_feature_yaml(feature_name, feature_meta)
            except ValidationError as e:
                # TODO maybe handle the failure case more gracefully.
                # TODO reuse code from the messages module to print error messages consistently
                print(f"Error: {e}", sys.stderr)
                return

            self.include_feature(feature_name, feature_meta)

    def load_feature_module(self, mod_path: str):
        """Imports a single Dysart feature library into this Project's
        """
        mod_path = os.path.expanduser(mod_path)
        module_name = os.path.splitext(os.path.basename(mod_path))[0]
        spec = importlib.util.spec_from_file_location(
            module_name, mod_path
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # add the module to the global namespace
        self.modules.update({module_name: mod})

    def __validate_feature_yaml(self, feature_name: str, feature_meta: Dict):
        """Checks the correctness of a feature's metadata in its project file,
        raising a ValidationError exception if it is invalid.

        Args:
            feature_name (str): The name of the feature to be validated
            feature_meta (dict): Metadata about a feature to be validated

        Returns:
            None

        """
        if 'class' not in feature_meta:
            raise ValidationError('Feature `{}` is missing a `class` field in project {}'.format(
                feature_name, self.path
            ))
        if 'id' not in feature_meta:
            raise ValidationError('Feature `{}` is missing an `id` field in project {}'.format(
                feature_name, self.path
            ))
        # TODO: `load-time check` of correct parents

    def get_feature_class(self, feature_class_name: str):
        """Given a description of a feature class like `'equs_features.QubitSpectrum'`,
        returns the class `equs_features.QubitSpectrum`.

        TODO: there might be a better way to do this without calling 'eval', but I'm not
        aware of it. Think about it next time you see this message.
        """
        class_path = feature_class_name.split('.')
        item = self.modules[class_path[0]]  # resolve the name starting with the module
        for name in class_path[1:]:
            item = getattr(item, name)
        return item

    def include_feature(self, feature_name: str, feature_meta: Dict):
        """Either load an existing document, if one exists, or create a new one and
        load it into this project.

        Note that this kind of function is deemed unsafe by the mongoengine docs,
        since MongoDB lacks transactions. This might be an important design
        consideration, so keep an eye on this.

        The equivalent deprecated mongoengine function is called
        `get_or_create`.

        Args:
            feature_name (str): The name of the feature to be included.
            feature_meta (Dict): The configuration metadata of the feature.

        Returns:
            Feature of type feature_class.

        Raises:
            MultipleObjectsReturned: if multiple matching objects are found
            DoesNotExist: if the feature is not found

        """

        # need to resolve the class name to an actual class that can be
        # instantiated.
        # TODO error handling: what to do if you don't get a class?
        feature_class = self.get_feature_class(feature_meta['class'])
        # the database id of the feature
        feature_id = feature_meta['id']
        # get the key->id mapping of the feature's parents; default to empty dict
        feature_parents = feature_meta.get('parents', {})

        try:
            # Attempt to find this feature in the database
            feature = feature_class.objects.get(id=feature_id)
        except me.DoesNotExist:
            # If it isn't found, create one!
            feature = feature_class(id=feature_id)
            # If you're creating one, you should also attach its parents.
            feature.add_parents(feature_parents)
        except me.MultipleObjectsReturned:
            # Don't do anything yet; just propagate the exception
            raise me.MultipleObjectsReturned
        self.features[feature_name] = feature
