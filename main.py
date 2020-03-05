import os.path
from flask import Flask, render_template, request, jsonify, make_response
from SentimentAnalyzer import SentimentAnalyzer
from PropertyReader import PropertyReader

app = Flask(__name__)

env_props = PropertyReader().read_properties_file()

api_context = env_props.get('api_context')

@app.route(api_context)
def home():
    return make_response(jsonify({'error': 'Resource Not found'}), 404)

@app.route(api_context + '/analyze', methods = ['POST'])
def analyze():
    if request.method == 'POST':
        data = json.loads(request.data)
        url = data.get("url", None)
        if url is None:
            return make_response(jsonify({'error': 'URL parameter not available. check your request'}), 400)
        else:
            result = SentimentAnalyzer.sentiment_analyze_invoke(url)
            return make_response(jsonify({'result': result}), 200)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Resource Not found'}), 404)

if __name__ == "__main__":
    app.run(debug=True)

