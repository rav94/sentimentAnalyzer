import os.path
import json
import validators
from flask import Flask, render_template, request, jsonify, make_response
from SentimentAnalyzer import SentimentAnalyzer
from PropertyReader import PropertyReader

app = Flask(__name__)

env_props = PropertyReader().read_properties_file()

api_context = env_props.get('api_context')

@app.route(api_context)
def home():
    return make_response(jsonify({'success': 'Helath Check Up'}), 200)

@app.route(api_context + '/analyze', methods = ['POST'])
def analyze():
    if request.method == 'POST':
        print(request.data);

        data = json.loads(request.data)

        if "" in data:
            return make_response(jsonify({'error': 'Your request is empty, please send a valid request'}), 400)
        else:
            url = data.get("url", None)

            if url is None:
                return make_response(jsonify({'error': 'URL parameter not available. check your request'}), 400)

            else:
                if not validators.url(url):
                    return make_response(jsonify({'error': 'URL sent was not valid'}), 400)

                else:
                    result = SentimentAnalyzer(url).sentiment_analyze_invoke()

                    if (result["status"] and result["sentiment"]):
                        return make_response(jsonify({'status': True, 'details': 'Succesfully Analyzed', 'result': result["sentiment"]}), 200)
                    
                    else:
                        if (result["error"]):
                            return make_response(jsonify({'status': False, 'details': 'Internal Error Occured', 'error': result["error"]}), 500)
                        else:
                            return make_response(jsonify({'status': False, 'details': 'Internal Error Occured', 'error': "N/A"}), 500)
    
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Resource Not found'}), 404)

if __name__ == "__main__":
    app.run(debug=True)

