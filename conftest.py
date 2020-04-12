import pytest
from web import app, db, login_manager


@pytest.fixture
def client():
	'''
	This is an extremely simplified configuration for testing. I spent some hours trying to learn how 
	this can be improved:
		1. Most configurations first rely on having a create_app function for the main app while we don't currently have one. 
		2. After applying that, it seems useful to separate the client creation from the db setup, and then define a session-level setting that allows each test to run with a separate db whereas it is not the case with this configuration. We basically use our app but change its config to use a temporary db.
		3. Also, using a temp file as it was before did not work for me, it kept using our original db or throw errors. 
		4. I am not sure the teardown is clean here, since os.unlink(app.config['SQL..']) did not work when this is set to theh in-memory DB. So that might be another point for importvement. 
		
	For now I proceeded with creating some tests until someone else gets to have a look or I manage to learn a bit more.
	'''
	
	app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
	app.config['TESTING'] = True
	app.config['SECRET_KEY'] = 'test_key'

	with app.test_client() as client:
		db.create_all()
		yield client
		db.drop_all()

@pytest.fixture
def reset_db(scope='function'):
	'''A crude and probably imperfect way to reset the DB between consecutive tests'''
	db.drop_all()
	db.create_all()