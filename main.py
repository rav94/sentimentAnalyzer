import os.path
from flask import Flask, render_template, request, jsonify, make_response
from SentimentAnalyzer import SentimentAnalyzer
from PropertyReader import PropertyReader

app = Flask(__name__)

env_props = PropertyReader().read_properties_file()

@app.route(env_props.get('api_context'))
def home():
    return make_response(jsonify({'error': 'Resource Not found'}), 404)

@app.route(env_props.get('api_context') + '/analyze', methods = ['POST'])
def sentimentIdentifyer():
    if request.method == 'POST':
        #TODO
        return "Hello World!"

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Resource Not found'}), 404)

if __name__ == "__main__":
    app.run(debug=True)