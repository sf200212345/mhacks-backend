You will need to set up a python virtual environment for this section.
Use the following to create a virtual environment. Make sure you are inside the "backend" folder when doing this.
```
python3 -m venv venv
```

To activate/deactivate your virtual environment (make sure to always activate before running anything in "backend"!):
```
source venv/bin/activate
deactivate
```

To install dependencies (make sure you're inside your "backend" folder and your virtual environment has been activated!):
```
pip install -r requirements.txt
```

Make sure you add your google api key to a .env file locally. i.e. add the following line to a .env file in this folder:
```
GOOGLE_API_KEY={your api key}
```


To run your flask app locally (make sure your virtual environment is activated!):
```
flask run --debug -p 3000
```

This will run flask as a development server locally with the IP as localhost (127.0.0.1) and 3000 as the port. If the port 3000 is not available, run it on any available port and make sure to set the correct port on the frontend interface.


To run your flask app with an extenally visible server (accessing this from another device doesn't seem to work right now)
```
flask run --debug --host=0.0.0.0 
```