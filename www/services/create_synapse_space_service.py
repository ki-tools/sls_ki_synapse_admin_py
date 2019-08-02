import re
from www.core.synapse import Synapse
import synapseclient as syn


class CreateSynapseSpaceService(object):
    def __init__(self, project_name, emails=None):
        self.project_name = project_name
        self.emails = emails

    def execute(self):
        errors = []

        # TODO: Create the project et al...

        errors.append('Not Implemented')  # TODO: remove this.
        errors.append('Test Error')  # TODO: remove this.

        return errors
