![status](https://github.com/recourcefulcoder/SanicAPI/actions/workflows/commit-check.yml/badge.svg)
# SanicAPI
Test task for DimaTech company

### Description
This project is an asynchronous web-application written on Sanic, which implements endpoints for
primitive payment system functionality.

Go to:
- [Deployment](#deployment-guide)
  - [Deploying with Docker Compose](#deployment-using-docker-compose-recommended)
  - [Deploying Manually](#manual-deployment-without-docker-compose)
- [Documentation](#documentation)
  - [Environment variables](#environment-variables) 
  - [Migrations guide](#database-migrations)
  - [Notes on auth mechanism](#authentication-notes)
  - [Endpoint documentation](#endpoint-documentation)
- [Notes on testing](#testing-notes) (**MUST READ** before running)


### Deployment guide
You should take into account that following deployment guide is written for a test environment only,
and since default database migrations consider creating test admin and test user (and no valid mechanisms
for creating them in real production use were implemented).

With that mentioned, _let's deploy_!

#### Deployment using Docker Compose (Recommended) 
This is the easiest way to deploy an application

##### **Steps:**
1. Clone the repo
```bash
git clone https://github.com/recourcefulcoder/SanicAPI.git
cd SanicAPI 
```

2. Create an .env file, containing all required environment variables

Since it is a vulnerable (from a security point) action, pay attention not to expose this file 
in VCS/any other web-source - keep it locally on your machine.

3. Run docker compose:

Assuming you are in the root directory of the project:
```bash
docker compose up -d --build
```

4. Check the application is running

```bash
curl -X GET localhost:8000/
```

5. To stop the services:

```bash
docker compose down 
```

#### Manual deployment (without Docker Compose)
1. Install dependencies

Assuming you have python 3.10+ installed:
```bash
pip install -r requirements.txt
```

2. Create .env file in the root directory of the project

3. Set up PostgreSQL database

- Install PostgreSQL and start postgresql service
- Create a new database 
> [!WARNING]
> make sure your database auth credentials/name match with those declared in .env file!
- run database migrations using alembic (from root directory):
```bash
cd src
alembic upgrade head
```

4. Start the API 

From root directory of the project:
```bash
cd src
sanic server:create_app --host 0.0.0.0
```

5. Check the application is running

```bash
curl -X GET localhost:8000/
```

### Documentation
source code of an application is split to two packages - "app" and "database". 
- "app" contains main application logic -  endpoint definitions, auth instruments and 
other functions (stated in utils.py)
- "database" contains DB logic - definition of models and connection engine

besides of these, "src" directory contains:
- _alembic_ directory - for storing migrations
- _tests_ directory, containing application tests
- _config.py_ file, which stores application-level constants
- _server.py_ file, containing Sanic-factory function

#### Environment variables
+ **SANIC_SECRET** - value used for cryptographic purposes
+ **WEBHOOK_SECRET** - secret key used for webhook requests validation 
+ **HOST** defines host to be used for database connection; defaults to localhost; developers in
production mode are encouraged to set this variable to the name of docker service (for details see 
"**_deployment_**" section) 
+ **POSTGRES_DB** defines name of PostgreSQL database
+ **POSTGRES_PASSWORD** 
+ **POSTGRES_USER** 

#### Database migrations

In order to apply database migrations, from "src" directory run:

```bash
alembic upgrade head
```

Migration creates database and provides default test data:
+ _admin user_ (password: "admin", email: "admin@example.com")
+ _non-admin user_ (full_name: "John Doe", email: "default@example.com", password: "Harmonica52!")
+ _default account_ (attached to "John Doe", balance is 0.0)

#### Authentication notes
JWT is chosen as an authentication backend (no refresh tokens, only short-living access tokens) 

user's email is chosen as a value for "sub" parameter of JWT payload

#### Endpoint documentation
Endpoints are splitted into three [blueprints](https://sanic.dev/en/guide/best-practices/blueprints.html):
+ **auth**, handling only login
+ **main**, handling main user functionality
+ **admin_bp**, handling admin functionality
+ **webhook**, handling single "webhook" endpoint, processing side paying system request

Handlers:
##### main
+ get_personal_data(request) - handles "/me" endpoint, i.e. getting user's personal information (email and full name)
+ get_account_data(request) - handles "/accounts" endpoint; gives user information about it's accounts 
+ get_transactions(request) - handles "/transactions" endpoint; gives user information about received transactions

##### auth
+ login(request) - handles "auth/login" endpoint; accepts json-object with auth credentials (containing keys 
"email" and "password") and returns JWT access token on valid credentials

##### admin_bp
+ create_user(request) - accepts json object with required fields "password" and "email";
    optional are "full_name" and "is_admin"; 

"email" must be valid email, "is_admin" (if provided)
must be True, yes, y or 1 if "TRUE" must be set, anything else is considered false
"full_name" must be a set of words consisting of english ASCII-only letters
"passwrod" must be a string, consisting only of english ASCI symbols, digits and special symbols 

if data is valid, creates new user and returns information about it in json format
+ UserManipulationView.put(request, id: int) - accepts json-object, where looks only for 
    following "checkup fields" - "password", "full_name", "email", "is_admin"; other keys of json-object
    will be ignored. Sent JSON must contain at least one of "checkup fields"; if all checkup fields 
    provided contain valid value, user on given id will be updated   
    
##### webhook
+ process_payment(request) - contains logic of webhook processing; accepts json-object, validates signature and on valid 
objects writes transaction to the database and credits money to target account.


### Testing notes

> [!CAUTION]
> DO NOT run tests on real production database, as it may delete crucial user data!
> to run tests, use specially created test database.

Best approach for running tests if to run tests from set-up container, as it uses test migration
with test data.

To run tests from container, execute following commands from root directory of the project:

```bash
docker compose up --build -d
docker-compose exec payment-app bash -c "cd src && python -m pytest"
docker compose down --volumes
```

make sure to write correct name of application service; by default (is defined in current veresion
of docker-compose.yaml) it is "payment-app".

However, you can run tests without docker - in order to do that, set up a test database 
1. Create test postgresql database
2. Migrate using alembic

from src directory run
```bash
alembic upgrade head
```
3. Provide valid credentials for connecting to TEST DATABASE in your .env file

> [!CAUTION]
> Avoiding this step may violate your data in real database! Pay attention to provide credentials 
> for TEST database, not development

4. Run tests

from src directory run:
```bash
python -m pytest
```
