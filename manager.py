import json

class Manager:

    def __init__(credentials, settings):

        self.credentials = self.credentials(credentials)
        self.settings(settings)    

    def credentials():
        #
        with open('credentils.json') as f:
            j = json.load(f)
            print(j)
    def settings():
        #
