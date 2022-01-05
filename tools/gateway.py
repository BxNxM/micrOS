# https://www.geeksforgeeks.org/python-build-a-rest-api-using-flask/
# https://stackoverflow.com/questions/48095713/accepting-multiple-parameters-in-flask-restful-add-resource
# using flask_restful
from flask import Flask, jsonify, request
from flask_restful import Resource, Api

# creating the flask app
app = Flask(__name__)
# creating an API object
api = Api(app)


# making a class for a particular resource
# the get, post methods correspond to get and post requests
# they are automatically mapped by flask_restful.
# other methods include put, delete, etc.
class Hello(Resource):

    # corresponds to the GET request.
    # this function is called whenever there
    # is a GET request for this resource
    def get(self):
        manual = {'micrOS gateway': 'v0.1',
                  '/list': 'List known devices.',
                  '/search': 'Search devices',
                  '/status': 'Get all device status',
                  '/sendcmd/<device>/<cmd>': 'Send command to the selected device. Use + instead of space.'}
        return jsonify(manual)

    # Corresponds to POST request
    #def post(self):
    #    data = request.get_json()  # status code
    #    return jsonify({'data': data}), 201


# another resource to calculate the square of a number
class SendCmd(Resource):

    def get(self, device, cmd):
        cmd_list = cmd.split('+')
        response = None
        return jsonify({'cmd': cmd_list, 'device': device, 'response': response})


class ListDevices(Resource):

    def get(self):
        device_list = {'uid': ['IP', 'PORT', 'FUID']}
        return jsonify({'devices': device_list})


class SearchDevices(Resource):

    def get(self):
        state = ('DONE', 'IN_PROGRESS', 'FAILED')
        device_list = {'uid': ['IP', 'PORT', 'FUID']}
        return jsonify({'devices': device_list, 'action': 'search', 'state': state[0]})


class DeviceStatus(Resource):

    def get(self):
        state = ('DONE', 'IN_PROGRESS', 'FAILED')
        device_list = {'uid': ['IP', 'PORT', 'FUID']}
        return jsonify({'devices': device_list, 'action': 'status', 'state': state[0]})


# adding the defined resources along with their corresponding urls
api.add_resource(Hello, '/')
api.add_resource(ListDevices, '/list/')
api.add_resource(SearchDevices, '/search/')
api.add_resource(DeviceStatus, '/status')
api.add_resource(SendCmd, '/sendcmd/<string:device>/<string:cmd>')

# driver function
if __name__ == '__main__':
    app.run(debug=True)

