# Welcome to CS162 Final Project

## Clone Repository

### Make Project Directory
```bash
git clone https://github.com/minerva-schools/cs162-habit.git
```

## Setup Local Environment

### Install Dependencies

1. Install python3 and pip3

```bash
$ brew install python3
```

2. Install virutalenv

```bash
$ pip3 install virtualenv
```

### Run Virtual Environment

3. Create virtualenv

```bash
$ virtualenv -p python3 venv
```
OR
```bash
$ python3 -m venv venv
```

4. Activate virtualenv
```bash
$ source venv/bin/activate
```
Or, if you are **using Windows** - [reference source:](https://stackoverflow.com/questions/8921188/issue-with-virtualenv-cannot-activate)

$ venv\Scripts\activate

5. Install dependencies inside virtual environment
```bash
(venv) $ pip3 install -r requirements.txt
```

6. Deactivate virtual environment
```bash
$ deactivate
```

## Environment Variables

All environment variables are stored within the `.env` file and loaded with dotenv package.

**Never** commit your local settings to the Github repository!

## Run Application

Start the server by running:

    $ export FLASK_ENV=development
    $ export FLASK_APP=web
    $ python3 -m flask run

Navigate to [localhost:5000](localhost:5000), you should see "Hello World!".

## Unit Tests
To run the unit tests use the following commands:

    $ python3 -m venv venv_unit
    $ source venv_unit/bin/activate
    (venv_unit) $ pip3 install -r requirements-unit.txt
    (venv_unit) $ export SQLALCHEMY_DATABASE_URI='sqlite:///web.db'
    (venv_unit) $ pytest unit_test
    (venv_unit) $ deactivate

All tests should pass.

Note: this is a seperate virtual environment!

## Integration Tests
Start by running the web server in a separate terminal.

Now run the integration tests using the following commands:

    $ python3 -m venv venv_integration
    $ source venv_integration/bin/actvate
    (venv_integration) $ pip3 install -r requirements-integration.txt
    (venv_integration) $ pytest integration_test
    (venv_integration) $ deactivate

All tests should pass.

Note: this is a seperate virutal environment!

## Contributors
- Zane Sand: Team Lead / DevOps & Backend
- Tom Kremer: Backend
- Zineb Salimi: Backend
- Nour Elkhalawy: Design / Backend
