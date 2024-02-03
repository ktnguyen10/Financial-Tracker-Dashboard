from financial_dashboard import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8083, threaded=True, debug=True, use_reloader=False, load_dotenv=True)
