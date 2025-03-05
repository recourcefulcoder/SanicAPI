# SanicAPI
Test task for DimaTech company


### Environmental variables
+ **SANIC_SECRET** - value used for cryptographic purposes
+ **WEBHOOK_SECRET** - secret key used for webhook requests validation 
+ **HOST** defines host to be used; defaults to localhost
+ **POSTGRES_DB** defines name of PostgreSQL database
+ **POSTGRES_PASSWORD** 
+ **POSTGRES_USER** 


In order to apply database migrations, from "src" directory run:

```bash
alembic upgrade head
```

Migration creates database and provides default test data:
+ _admin user_ (password: "admin", email: "admin@example.com")
+ _non-admin user_ (full_name: "John Doe", email: "default@example.com", password: "Harmonica52!")
+ _default account_ (attached to "John Doe", balance is 0.0)


### Authentication notes
JWT is chosen as a authentication backend (no refresh tokens, only short-living access tokens) 

user's email is chosen as a value for "sub" parameter of JWT payload


### Endpoint documentation
Endpoints are splitted into three [blueprints](https://sanic.dev/en/guide/best-practices/blueprints.html):
+ **auth**, handling only login
+ **main**, handling main user functionality
+ **admin_bp**, handling admin functionality
+ **webhook**, handling single "webhook" endpoint, processing side paying system request

##### admin_bp
+ create_user(request) - accepts json object with required fields "password" and "email";
    optional are "full_name" and "is_admin"
    if data is valid, creates new user and returns information about it in
    json format
+ UserManipulationView.put(request, id: int) - accpets json-object, where looks only for 
    following "checkup fields" - "password", "full_name", "email", "is_admin"; other keys of json-object
    will be ignored. Sent JSON must contain at least one of "checkup fields"; if all checkup fields 
    provided contain valid value, user on given id will be updated   
    
##### webhook
+ process_payment(request) - contains logic of webhook processing
