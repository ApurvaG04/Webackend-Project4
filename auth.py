import dataclasses
import collections
from operator import itemgetter
import databases
from quart import Quart, g, request, jsonify, abort
from quart_schema import validate_request, RequestSchemaValidationError, QuartSchema
import sqlite3
import toml


app = Quart(__name__)
QuartSchema(app)
app.config.from_file(f"./etc/{__name__}.toml", toml.load)

@dataclasses.dataclass
class userData:   
    username: str
    password: str

async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL"])
        # db = g._sqlite_db = databases.Database('sqlite+aiosqlite:/wordle.db')
        await db.connect()
    return db

@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()

@app.errorhandler(401)
def unauthorized(e):
    return {"error": str(e).split(':', 1)[1][1:]}, 401, {"WWW-Authenticate": "Basic realm"}

@app.errorhandler(404)
def unauthorized(e):
    return {"error": str(e).split(':', 1)[1][1:]}, 404

@app.route("/users/all", methods=["GET"])
async def all_users():
    db = await _get_db()
    all_users = await db.fetch_all("SELECT * FROM userData;")

    return list(map(dict, all_users))  


#------------Registering a new user-----------------#

@app.route("/register/", methods=["POST"])
@validate_request(userData)
async def register_user(data):
    db = await _get_db()  
      
    userData = dataclasses.asdict(data)   
    
    try:
        username = await db.execute(
            """
            INSERT INTO userData(username, password)
            VALUES(:username, :password)
            """,
            userData,
        )
    except sqlite3.IntegrityError as e:
        abort(409, e)
    
    userData["username"] = username     
    return jsonify({"statusCode": 200, "message": "Successfully registered!"})

@app.errorhandler(RequestSchemaValidationError)
def bad_request(e):
    return {"error": str(e.validation_error)}, 401

@app.errorhandler(409)
def conflict(e):
    return {"error": str(e)}, 409


SearchParam = collections.namedtuple("SearchParam", ["name", "operator"])
SEARCH_PARAMS = [
    
    SearchParam(
        "username",
        "=",
    ),
    SearchParam(
        "password",
        "=",
    ),
    
]

#-------------Authenticating the credentials for Login----------------
@app.route('/auth', methods=['GET'])
async def authenticate():
    # query_parameters = request.args
    # #db = await _get_db()         
    
    # sql = "SELECT username,password FROM userData"
    # conditions = []
    # values = {}

    # for param in SEARCH_PARAMS:
    #     if query_parameters.get(param.name):
    #         if param.operator == "=":
    #             conditions.append(f"{param.name} = :{param.name}")
    #             values[param.name] = query_parameters[param.name]               

    # if conditions:
    #     sql += " WHERE "
    #     sql += " AND ".join(conditions)

    # app.logger.debug(sql)

    # db = await _get_db()
    # results = await db.fetch_all(sql, values)  
   
    
    # my_list= list(map(dict, results))    
    # pwd = list(map(itemgetter('password'), my_list))
    # name = list(map(itemgetter('username'), my_list))    
   
    # result_dict= {}

    # for key in name:
    #      for value in pwd:
    #          result_dict[key] = value
    #          pwd.remove(value)
    #          break      
    

    # for key in result_dict:
    #     if(request.authorization.password==result_dict[key] and request.authorization.username==key  ) :        
    #         return jsonify({"authenticated": "true"})   
    # # WWW-Authenticate error for 401
    # return jsonify({"statusCode": 401, "error": "Unauthorized", "message": "Login failed !"}), 401
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        abort(401, "Please provide a username and password")

    db = await _get_db()
    user = await db.fetch_one("SELECT * FROM userdata WHERE username=:username", {"username": auth.username})

    if not user:
        abort(401, "Incorrect username or password")

    if user[1] != auth.password:
        abort(401, "Incorrect username or password")

    return {"authentication:": True}, 200
