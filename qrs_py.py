import requests
import json
import csv
import random
import string


requests.packages.urllib3.disable_warnings()


def set_xrf():
    characters = string.ascii_letters + string.digits
    return ''.join(random.sample(characters, 16))

xrf = set_xrf()


class ConnectQlik:
    """
    Instantiates the Qlik Repository Service Class
    """

    def __init__(self, server, certificate, root):
        """
        Establishes connectivity with Qlik Sense Repository Service
        :param server: servername.domain:4242
        :param certificate: path to client.pem and client_key.pem certificates
        :param root: path to root.pem certificate
        """
        self.server = server
        self.certificate = certificate
        self.root = root

    @staticmethod
    def headers():
        return {
            "X-Qlik-XrfKey": xrf,
            "Accept": "application/json",
            "X-Qlik-User": "UserDirectory=Internal;UserID=sa_repository",
            "Content-Type": "application/json"
        }

    def get_servicestate(self):
        """
        Gets the service state of the QRS
        """
        endpoint = 'qrs/servicestatus'
        response = requests.get('https://%s/%s?xrfkey=%s' % 
                                (self.server, endpoint, xrf),
                                headers=self.headers(), 
                                verify=self.root, 
                                cert=self.certificate)
        return (response.text)
        if response.text == 0:
            return ('Initializing')
        elif response.text == 1:
            return ('Certificates not installed')
        else:
            return ('Running')

    def get_about(self):
        """
        Gets Qlik Sense Server information
        """
        endpoint = 'qrs/about'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def get_dataconnection(self, param, value):
        """
        Gets the data connections from the Qlik Sense Server
        :param param: Filter detail, Enter None for no filter
        :param value: Value of the filter
        """
        if param is None:
            endpoint = 'qrs/dataconnection'
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            return (response.text)
        else:
            endpoint = "qrs/dataconnection?filter=%s '%s'" % (param, value)
            response = requests.get('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            dataconnection = json.loads(response.text)
            return dataconnection

    def get_user(self, param, value):
        """
        Gets the users from Qlik Sense
        :param param: Filter detail, Enter None fo no filter
        :param value: Value of the filter
        :return: The list of users
        """
        if param is None:
            endpoint = 'qrs/user'
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            jresp = json.loads(data)
            return (jresp)
        else:
            endpoint = "qrs/user?filter=%s '%s'" % (param, value)
            response = requests.get('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            jresp = json.loads(data)
            return (jresp)

    def delete_user(self, id):

        endpoint = 'qrs/user/%s' % id
        response = requests.delete('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)

        return (response.text)    

    @staticmethod
    def jsonfieldnames(filename):
        """
        Returns the header row of the file to create the structure of the json file
        :param filename: Path and filename of the text or csv file to be imported
        """
        jsonfieldnames = []
        with open(filename, 'rt') as f:
            for row in csv.reader(f, delimiter=','):
                jsonfieldnames.append(row)
        return jsonfieldnames[0]

    @staticmethod
    def csvrowcount(filename):
        """
        Returns the count of rows minus the header of the file
        :param filename: Path and filename of the text or csv file to be imported
        """
        rowcount = 0
        with open(filename, 'rt') as f:
            for row in f:
                rowcount += 1
        return rowcount - 1

    def concsvjson(self, filename):
        """
        Converts the text or csv file to a JSON file and returns the path and name of the file
        :param filename: Path and filename of the text or csv file to be imported
        """
        jsonfieldnames = self.jsonfieldnames(filename)
        csv_file = filename
        json_file = csv_file.split(".")[0] + ".json"
        with open(csv_file, 'rt') as f:
            next(f)
            csv_reader = csv.DictReader(f, jsonfieldnames)
            with open(json_file, 'w') as jf:
                data = json.dumps([r for r in csv_reader])
                jf.write(data)
        return json_file

    def import_users(self, filename):
        """
        Posts users from file into Qlik Sense
        :param filename: Path and filename to txt or csv file containing users
        :example import_users(r'c:\\some\\folder\\file.txt')
        """
        if self.csvrowcount(filename) == 1:
            endpoint = 'qrs/user'
        else:
            endpoint = 'qrs/user/many'
        with open(self.concsvjson(filename), 'rb') as users:
            response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                     headers=self.headers(), data=users, verify=self.root, cert=self.certificate)
        return (response.text)

    def get_license(self):
        """
        Gets the Qlik Sense Server license details and returns the ID
        :return: License ID
        """
        try:
            endpoint = 'qrs/license'
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            resp = json.loads(data)
            return resp['id']
        except TypeError:
            return ('Server not licensed')

    def get_lef(self, serial, control, user, organization):
        """
        Gets Qlik Sense LEF information from the Qlik Server (requires web access)
        """
        endpoint = 'qrs/license/download?serial=%s&control=%s&user=%s&org=%s' % (serial, control, user, organization)
        response = requests.get('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def set_license(self, control, serial, name, organization, lef):
        """
        Licenses Qlik Sense Server
        :param control: License control number
        :param serial: License serial number
        :param name: License name
        :param organization: License organization
        :lef: Set to None if server is internet connected else format as this
        lef = "line1\{r}\{n}line2\{r}\{n}line3\{r}\{n}line4\{r}\{n}line5\{r}\{n}line6\{r}\{n}line7" (remove {})
        """
        if lef is None:
            endpoint = 'qrs/license?control=%s' % control
            data = {
                "serial": serial,
                "name": name,
                "organization": organization
            }
            response = requests.post('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                     headers=self.headers(), json=data, verify=self.root, cert=self.certificate)
            return (response.text)
        else:
            endpoint = 'qrs/license?control=%s' % control
            data = {
                "serial": serial,
                "name": name,
                "organization": organization,
                "lef": lef
            }
            response = requests.post('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                     headers=self.headers(), json=data, verify=self.root, cert=self.certificate)
            return (response.text)

    def delete_license(self):
        """
        Deletes the license from Qlik Sense Server
        """
        licenseid = self.get_license()
        endpoint = 'qrs/license/%s' % licenseid
        response = requests.delete('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                        headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def get_app(self, param, value):
        """
        Gets the applications from Qlik Sense Server
        :param param: None for no filter, filter values otherwise. eg stream.name eq
        :param value: Value to filter on.
        """
        if param is None:
            endpoint = 'qrs/app'
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            jresp = json.loads(data)
            return (jresp)
        else:
            endpoint = "qrs/app?filter=%s '%s'" % (param, value)
            response = requests.get('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            jresp = json.loads(data)
            return (jresp)

    def get_app_count(self):
        """
        Gets the count of applications from the Qlik Sense Server
        """
        endpoint = 'qrs/app/count'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def import_app(self, name, filename):
        """
        Imports a binary QVF Qlik Sense application to Qlik Sense Server
        :param name: The name of the application that will be displayed in Qlik Sense
        :param filename: The path and filename for the QVF file
        """
        endpoint = 'qrs/app/upload?name=%s' % name
        headers = {
            "X-Qlik-XrfKey": xrf,
            "Accept": "application/json",
            "X-Qlik-User": "UserDirectory=Internal;UserID=sa_repository",
            "Content-Type": "application/vnd.qlik.sense.app",
            "Connection": "Keep-Alive"
        }
        with open(filename, 'rb') as app:
            response = requests.post('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                     headers=headers, data=app, verify=self.root, cert=self.certificate)
        return (response.text)

    def get_customproperty(self):
        """
        Gets the custom properties from the Qlik Sense Server
        """
        endpoint = 'qrs/custompropertydefinition'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def get_tag(self):
        """
        Gets the Tags from the Qlik Sense Server
        """
        endpoint = 'qrs/tag'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def import_tag(self, filename):
        """
        Imports Tags from a text or csv file
        :param filename: The path and filename of the text or csv file
        :usage import_tag(r'c:\\some\\folder\\file.txt')
        """
        if self.csvrowcount(filename) == 1:
            endpoint = 'qrs/tag'
        else:
            endpoint = 'qrs/tag/many'
        with open(self.concsvjson(filename), 'rb') as tags:
            response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                     headers=self.headers(), data=tags, verify=self.root, cert=self.certificate)
        return (response.text)

    def get_task(self):
        """
        Gets the tasks from the Qlik Sense Server
        """
        endpoint = 'qrs/task'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def start_task(self, taskid):
        """
        Start a task (for example, a reload task), identified by {id}, so that it runs on a Qlik
                                                                Sense Scheduler Service (QSS).
        :param taskid: id of the task
        """
        endpoint = 'qrs/task/%s/start' % taskid
        response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                 headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.status_code)

    def get_rule(self):
        """
        Gets the security rules from the Qlik Sense Server
        """
        endpoint = 'qrs/systemrule'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def get_userdirectory(self):
        """
        Gets the user directories configured on the Qlik Sense Server
        """
        endpoint = 'qrs/userdirectory'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        data = response.text
        jresp = json.loads(data)
        return (jresp)

    def get_exportappticket(self, appid):
        """
        Gets a one time ticket to export an application
        :param appid: id of the application
        """
        endpoint = 'qrs/app/%s/export' % appid
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        resp = json.loads(response.text)
        return resp['value']

    def export_app(self, appid, filepath, filename):
        """
        Exports the Qlik Sense application
        :param appid: The application id name to export
        :param filepath: The path to the file
        :param filename: The path and filename to export the application to
        :usage: export_app(r'8dadc1f4-6c70-4708-9ad7-8eda34da0106', r'c:\\some\folder\\', 'app.qvf')
        """
        ticket = self.get_exportappticket(appid)
        endpoint = 'qrs/download/app/%s/%s/%s' % (appid, ticket, filename)
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        if response.status_code == 200:
            with open(filepath + filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
        print (response.status_code)
        print ('Application: %s written to path: %s' % (appid, filepath))

    def get_extension(self):
        """
        Gets the extensions installed on Qlik Sense
        """
        endpoint = 'qrs/extension'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def import_extension(self, filename):
        """
        Imports the extension to Qlik Sense
        :param filename: The path and filename of the extension (make sure its a zip archive)
        :usage: import_extension(r'c:\\some\folder\\file.zip')
        """
        endpoint = 'qrs/extension/upload'
        with open(filename, 'rb') as extension:
            response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                     headers=self.headers(), data=extension, verify=self.root, cert=self.certificate)
        return (response.text)

    def import_customproperty(self, filename):
        """
        Imports custom properties into Qlik Sense
        :param filename: Path and filename to JSON file
        "App","ContentLibrary","DataConnection","EngineService","Extension","ProxyService","ReloadTask",
        "RepositoryService","SchedulerService","ServerNodeConfiguration","Stream","User","UserSyncTask",
        "VirtualProxyConfig"
        {
            "name": "FOO",
            "valueType": "BAR",
            "choiceValues":
                ["FOO",
                "BAR"],
            "objectTypes":
                ["App",
                 "RepositoryService"]}
        :usage: import_customproperty(r'c:\\some\\folder\\file.txt')
        """
        endpoint = 'qrs/custompropertydefinition/many'
        with open(filename) as customproperties:
            cpjson = json.loads(customproperties.read())
            response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                          headers=self.headers(), json=cpjson, verify=self.root, cert=self.certificate)

        return (response.text)

    def copy_app(self, name, appid):
        """
        Copies an application within Qlik Ssnese
        :param name: Name of the new application
        :param appid: ID of the Qlik Sense application to copy
        """

        endpoint = 'qrs/app/%s/copy?name=%s' % (appid, name)
        response = requests.post('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                      headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def publish_app(self, appid, streamid, name):
        """
        Publishes the Qlik Sense application to the selected stream with the name
        :param appid: ID of the application to publish
        :param stream: Stream name to publish the application to
        :param name: Name of application once published
        """
        endpoint = 'qrs/app/%s/publish?stream=%s&name=%s' % (appid, streamid, name)
        response = requests.put('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def delete_app(self, appid):
        """
        Deletes a Qlik Sense application
        :param appid: Name of the application to delete
        """
        endpoint = 'qrs/app/%s' % appid
        requests.delete('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                        headers=self.headers(), verify=self.root, cert=self.certificate)

    def get_stream(self, param, value):
        """
        Gets the Qlik Streams on the Qlik Sense Server or if filter used returns the Streams ID
        :param param: Allows filtering on the name of the stream. Use None for no filter
        :param value: the value of the filter
        :return: id of stream
        """
        if param is None:
            endpoint = 'qrs/stream'
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            jresp = json.loads(data)
            return (jresp)
        else:
            endpoint = "qrs/stream?filter=%s '%s'" % (param, value)
            response = requests.get('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            jresp = json.loads(data)
            return (jresp)

    def add_stream(self, name):
        """
        Adds a new Stream to the Qlik Sense server
        :param name: The name of the new Stream
        """
        data = {"name": name}
        endpoint = 'qrs/stream'
        response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                 headers=self.headers(), json=data, verify=self.root, cert=self.certificate)
        return (response.text)

    def get_qliknode(self):
        """
        Gets the server node configuration
        """
        endpoint = 'qrs/servernodeconfiguration'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def delete_stream(self, id):
        """
        Removes a Stream from the server, applications become unpublished
        :param id: ID of the stream to delete
        """
        endpoint = 'qrs/stream/%s' % id
        response = requests.delete('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                   headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.status_code)

    def delete_tag(self, id):
        """
        Removes a tag
        :param id: ID of the tag to delete
        """
        endpoint = 'qrs/tag/%s' % id
        response = requests.delete('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                   headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.status_code)

    def delete_customproperty(self, id):
        """
        Removes a custom property
        :param id: id of the custom property to delete
        """
        endpoint = 'qrs/custompropertydefinition/%s' % id
        response = requests.delete('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                   headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.status_code)

    def sync_userdirectory(self, id):
        """
        Synchronises the user directory specified by the id
        :param id: id of the user directory
        """
        endpoint = 'qrs/userdirectoryconnector/syncuserdirectories'
        udid = '["%s"]' % id
        response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                 headers=self.headers(), data=udid, verify=self.root, cert=self.certificate)
        return (response.status_code)

    def get_engineservice(self, id):
        """
        Gets the details of the engine service specified by the id
        :param id: id of the engine service
        """
        endpoint = 'qrs/engineservice/%s' % id
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def export_certificates(self, machinename, certificatepassword, includesecret, exportformat):
        """
        Exports certificates from the Central Node - saved to C:\ProgramData\Qlik\Sense\Repository\Exported Certificates
        :param machinename: Computername to link to the certificates
        :param certificatepassword: Password to secure certificate private key
        :param includesecret: Include private key (True, False)
        :param exportformat: Format of export (Windows, Pem)
        """
        data = {"machineNames": [machinename], "certificatePassword": certificatepassword,
                "includeSecretsKey": includesecret, "ExportFormat": exportformat}
        endpoint = 'qrs/certificatedistribution/exportcertificates'
        response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                 headers=self.headers(), json=data, verify=self.root, cert=self.certificate)
        if 200 <= response.status_code < 300:
            return ('Certificates exported')

    def get_serverconfig(self):
        """
        Gets the local server configuration container
        """
        endpoint = 'qrs/servernodeconfiguration/local'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def get_emptyserverconfigurationcontainer(self):
        """
        Creates anf empty server configuration container
        """
        endpoint = 'qrs/servernodeconfiguration/container'
        response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def add_node(self, name, hostname, engineenabled, proxyenabled, schedulerenabled, printingenabled):
        """
        Adds a node to an existing Qlik Sense site
        :param name: The name of the node
        :param hostname: server hostname / FQDN
        :param engineenabled: Booleen value for whether new node has an engine
        :param proxyenabled: Booleen value for whether new node has an proxy
        :param schedulerenabled: Booleen value for whether new node has an schedulder
        :param printingenabled: Booleen value for whether new node has printing
        """
        endpoint = 'qrs/servernodeconfiguration/container'
        data = {"configuration": {"name": name, "hostName": hostname, "engineEnabled": engineenabled,
                                  "proxyEnabled": proxyenabled, "schedulerEnabled": schedulerenabled,
                                  "printingEnabled": printingenabled}}
        container = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                  headers=self.headers(), json=data, verify=self.root, cert=self.certificate)
        data = container.text
        jdata = json.loads(data)
        return jdata["configuration"]["id"]

    def add_dataconnection(self, username, password, name, connectionstring, conntype):
        """
        Adds a data connection to Qlik Sense
        :param username: The user the data connection will connect using
        :param password: The password of the user to connect
        :param name: The name of the data connection
        :param connectionstring: The connection string
        :param conntype: The type of connection
        :return:
        """
        endpoint = 'qrs/dataconnection/'
        data = {
            "username": username,
            "password": password,
            "name": name,
            "connectionstring": connectionstring,
            "type": conntype
        }
        response = requests.post('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                 headers=self.headers(), json=data, verify=self.root, cert=self.certificate)
        return (response.text)

    def migrate_app(self, appid):
        """
        This process is usually automatically performed after upgrades, however if the automated process fails this function
        can be used.
        :param appid: ID of the application to migrate
        :return: HTTP status code
        """
        endpoint = 'qrs/app/%s/migrate' % appid  
        response = requests.put('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.status_code) 

    def ping_proxy(self):
        """
        This function uses the QPS API to ping the anonymous endpoint /qps/user.  This allows the user 
        to know whether the Qlik Sense Proxy is operational.
        :return: HTTP status code
        """
        server = self.server
        qps = server[:server.index(':')]
        endpoint = '/qps/user'
        try:
            response = requests.get('https://%s/%s/' % (qps, endpoint), verify=self.root, cert=self.certificate)
            return (response.status_code)
        except requests.exceptions.RequestException as exception:
            return ('Qlik Sense Proxy down')

    def get_useraccesstype(self, id):
        """
        Displays the user access information (tokens).
        :param id: The ID of the user access
        :return: JSON object describing the user access token
        """
        if id is None: 
            endpoint = 'qrs/license/useraccesstype'
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)  
            return (response.text)
        else:
            endpoint = 'qrs/license/useraccesstype/%s' % id
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            return (response.text)

    def delete_useraccesstype(self, id):
        """
        Deletes the user access type (sets allocated to Quarantined)
        :param id: The ID of the user access
        :return: JSON object
        """
        endpoint = 'qrs/license/useraccesstype/%s' % id
        response = requests.delete('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.text)

    def get_appobject(self, objid):
        """
        Gets app objects from Qlik Sense Server
        :param: objid: The objectID of the application object (None for all)
        :return: Returns app objects
        """
        if objid is None:
            endpoint = 'qrs/app/object'
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            jresp = json.loads(data)
            return (jresp)
        else:
            endpoint = 'qrs/app/object/%s' % objid
            response = requests.get('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                    headers=self.headers(), verify=self.root, cert=self.certificate)
            data = response.text
            jresp = json.loads(data)
            return (jresp)
   
    def publish_appobject(self, objid):
        """
        Publishes an app object to community sheets
        :param: objid: The objectID of the application object
        :return: HTTP Status Code
        """
        endpoint = 'qrs/app/object/%s/publish' % objid
        response = requests.put('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.status_code)

    def unpublish_appobject(self, objid):
        """
        Unpublishes an app object from community sheets
        :param: objid: The objectID of the application object
        :return: HTTP Status Code
        """
        endpoint = 'qrs/app/object/%s/unpublish' % objid
        response = requests.put('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.status_code)

    def delete_appobject(self, objid):
        """
        Deletes an app object from Qlik Sense Server
        :param: objid: The objectID of the application object
        :return: HTTP Status Code
        """
        endpoint = 'qrs/app/object/%s' % objid
        response = requests.delete('https://%s/%s?xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        return (response.status_code)

    def get_apiendpoints(self, method):
        endpoint = 'qrs/about/api/description?extended=true&method=%s&format=JSON' % method
        response = requests.get('https://%s/%s&xrfkey=%s' % (self.server, endpoint, xrf),
                                headers=self.headers(), verify=self.root, cert=self.certificate)
        data = response.text
        jresp = data
        return (data)

if __name__ == '__main__':
    qrs = ConnectQlik('qs2.qliklocal.net:4242', ('C:/certs/qs2.qliklocal.net/client.pem',
                                      'C:/certs/qs2.qliklocal.net/client_key.pem'),
           'C:/certs/qs2.qliklocal.net/root.pem')
    if qrs.ping_proxy() == 200:
        print(qrs.get_about())

    x = print(qrs.get_servicestate())
