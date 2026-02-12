# A simple Flask app to test the setup on your iPad.
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    """Serves a simple test page."""
    return render_template('index.html')

if __name__ == '__main__':
    # Host 0.0.0.0 makes it accessible from other devices on your network.
    # Port 8080 is a common choice for web servers.
    app.run(host='0.0.0.0', port=8080)
