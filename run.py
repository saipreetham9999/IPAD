from brain import create_app

PORT = 8080
HOST = "0.0.0.0"


app = create_app()

if __name__ == '__main__':
    print(f"Brain starting on http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT, debug=False)
