from operator import itemgetter
import databases
from quart import Quart, g, request, jsonify, abort
from quart_schema import validate_request, RequestSchemaValidationError, QuartSchema
import sqlite3
import toml
import random
import uuid
import requests
from redis import Redis
from rq import Queue, Worker
from rq.registry import FailedJobRegistry
from rq.job import Job
import httpx
import itertools

app = Quart(__name__)
QuartSchema(app)
app.config.from_file(f"./etc/{__name__}.toml", toml.load)

async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        choose = itertools.cycle([1,2,3])
        if next(choose) == 1:
            db = g._sqlite_db = databases.Database(app.config["DATABASES"]["primary"])
        elif next(choose) == 2:
            db = g._sqlite_db = databases.Database(app.config["DATABASES"]["secondary_1"])
        else:
            db = g._sqlite_db = databases.Database(app.config["DATABASES"]["secondary_2"])
        await db.connect()
    return db
    
async def _get_primary_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["primary"])
        await db.connect()
    return db

@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()

@app.errorhandler(400)
def badRequest(e):
    return {"error": str(e).split(':', 1)[1][1:]}, 400

@app.errorhandler(401)
def unauthorized(e):
    return {"error": str(e).split(':', 1)[1][1:]}, 401, {"WWW-Authenticate": "Basic realm"}

@app.errorhandler(404)
def noGameFound(e):
    return {"error": str(e).split(':', 1)[1][1:]}, 404

#################################################
###### Forwarding Data To Leaderboard ###########
def send_data_to_redis_client(packet, callbackUrl):
    print(packet,callbackUrl)
    try:
        req = httpx.post(callbackUrl, json = packet)
        # req_test = httpx.get("http://127.0.0.1:5400/leaderboard")
        print(req.status_code)
    except requests.exceptions.HTTPError:
        return "Error", req.status_code

#################################################
############# WORKER FUCTION ####################
def worker(username, result, guesses, callbackUrl):
    redis = Redis()
    queue = Queue(connection=Redis())
    registry = FailedJobRegistry(queue=queue)
    packet = {"guesses": guesses,'result': result,'username':username}
    result = queue.enqueue(send_data_to_redis_client, packet, callbackUrl)
    for jobid in registry.get_job_ids():
        job = Job.fetch(jobid, connection=redis)
        print(jobid)                    
#################################################
#################################################

# @app.route("/test", methods=["GET"])
# async def what():
#     auth = request.authorization

#     if not auth or not auth.username or not auth.password:
#         abort(401, "you are not authorized bro")

#     print(auth.username)

#     return {"message": "test route", "id": uuid.uuid4()}, 200, {"WWW-Authenticate": "Basic realm=bad"}

    
# ---------------GAME API---------------

# ---------------HELPERS----------------

def getGuessState(guess, secret):
    word = guess
    secretWord = secret

    matched = []
    valid = []

    for i in range(len(secretWord)):
        correct = word[i] == secretWord[i]
        valid.append({"inSecret": correct, "wrongSpot": False, "used": True if correct else False})
        matched.append(correct)

    for i in range(len(secretWord)):
        currentLetter = secretWord[i]
        for j in range(len(secretWord)):
            if i != j:
                if not(matched[i]) and not(valid[j].get("used")):
                    if word[j] == currentLetter:
                        valid[j].update({"inSecret": True, "wrongSpot": True, "used": True})
                        matched[i] = True

    data = []
    index = 0

    for i in word:
        d = {}
        del valid[index]["used"]
        d[i] = valid[index]
        data.append(d)
        index += 1

    return data

async def gameStateToDict(game):
    db_select = await _get_db()
    secretWord = await db_select.fetch_one("SELECT word FROM correct WHERE id=:id", values={"id": game[2]})
    secretWord = secretWord[0]

    state = {"guessesLeft": game[3], "finished": True if game[4] == 1 else False, "gussedWords": []}

    timeGuessed = 6 - game[3]
    guessedWords = []

    for i in range(timeGuessed):
        word = game[i + 5]
        wordState = {word: getGuessState(word, secretWord)}
        guessedWords.append(wordState)

    state["gussedWords"] = guessedWords

    return state

async def updateGameState(game, word, db, finished = 0):
    numGuesses = game[3]
    nthGuess = 6 - numGuesses + 1

    sql = "UPDATE game SET guesses=:numGuess, finished=:finished, "
    suffix = "guess" + str(nthGuess) + "=:guess" + " WHERE id=:id"

    gameFinished = finished
    if numGuesses - 1 == 0:
        gameFinished = 1
    await db.execute(sql + suffix, values={"numGuess": numGuesses - 1, "id": game[0], "finished": gameFinished, "guess": word })

# ---------------CREATE NEW GAME---------------

@app.route("/game", methods=["POST"])
async def newGame():
    db_select = await _get_db()
    db_insert = await _get_primary_db()

    auth = request.authorization

    if not(auth) or not(auth.username):
        abort(401, "Please provide the username")

    username = auth.username

    words = await db_select.fetch_all("SELECT * FROM correct")
    num = random.randrange(0, len(words), 1)

    gameId = str(uuid.uuid4())
    data = {"gameId": gameId, "wordId": words[num][0], "username": username}

    await db_insert.execute(
        """
        INSERT INTO game(id, wordId, username)
        VALUES(:gameId, :wordId, :username)
        """,
        data)

    res = {"gameId": gameId, "guesses": 6}
    return res, 201

# @app.errorhandler(401)
# def unauthorized(e):
#     return {"error": str(e).split(':', 1)[1][1:]}, 401

# ---------------GUESS A WORD---------------

@app.route("/game/<string:gameId>", methods=["PATCH"])
async def guess(gameId):
    db_select = await _get_db()

    auth = request.authorization

    if not(auth) or not(auth.username):
        abort(401, "Please provide the username")

    username = auth.username

    body = await request.get_json()
    word = body.get("word").lower()

    if not(word):
        abort(400, "Please provide the guess word")

    game = await db_select.fetch_one("SELECT * FROM game WHERE id=:id", values={"id": gameId})

    # Check if game exists
    if not(game):
        abort(404, "Could not find a game with this id")

    if username != game[1]:
        abort(400, "This game does not belong to this user")

    # Check if game is finished
    if game[4] == 1:
        #message queue
        worker(auth.username, "You_Won", 6-game[3],"http://127.0.0.1:5400/reportgame")

        abort(400, "This game has already ended")

    # Check if word is valid
    if len(word) != 5:
        abort(400, "This is not a valid guess")

    wordIsValid = False

    # check if word is in correct table
    correct = await db_select.fetch_one("SELECT word FROM correct WHERE word=:word", values={"word": word})

    if not(correct):
        valid = await db_select.fetch_one("SELECT word FROM valid WHERE word=:word", values={"word": word})
        wordIsValid = valid is not None

    # invalid guess
    if not(wordIsValid) and not(correct):
        abort(400, "Guess word is invalid")

    # Not correct but valid
    secretWord = await db_select.fetch_one("SELECT word FROM correct WHERE id=:id", values={"id": game[2]})
    secretWord = secretWord[0]

    # guessed correctly
    if word == secretWord:
        await updateGameState(game, word, db_select, 1)
        
        #message queue
        worker(auth.username, "You_Won", 6-game[3],"http://127.0.0.1:5400/reportgame")

        return {"word": {"input": word, "valid": True, "correct": True}, 
        "numGuesses": game[3] - 1}

    await updateGameState(game, word, db_select, 0)
    data = getGuessState(word, secretWord)
    #message queue
    worker(auth.username, "You_Lost", 6-game[3],"http://127.0.0.1:5400/reportgame")
    return {"word": {"input": word, "valid": True, "correct": False}, 
        "gussesLeft": game[3] - 1, 
        "data": data}

# ---------------LIST GAMES FOR A USER---------------

@app.route("/my-games", methods=["GET"])
async def myGames():
    db_select = await _get_db()

    auth = request.authorization

    if not(auth) or not(auth.username):
        abort(401, "Please provide the username")

    username = auth.username

    games = await db_select.fetch_all("SELECT * FROM game WHERE username=:username", values={"username": username})

    gamesList = list(map(dict, games))
    res = []

    for game in gamesList:
        res.append({"gameId": game.get("id"), "guessesLeft": game.get("guesses"), "finished": True if game.get("finished") == 1 else False})

    return res

# @app.errorhandler(401)
# def unauthorized(e):
#     return {"error": str(e).split(':', 1)[1][1:]}, 401

# ---------------GET GAME STATE---------------

@app.route("/game/<string:gameId>", methods=["GET"])
async def getGame(gameId):
    db_select = await _get_db()

    game = await db_select.fetch_one("SELECT * FROM game WHERE id=:id", values={"id": gameId})

    if not(game):
        return {"message": "No game found with this id"}, 404
    
    return await gameStateToDict(game)


#Registering client URL into db
@app.route("/webhook", methods=["POST"])
async def register_client():

    res =  await request.get_json()
    callbackUrl = res.get("callbackUrl")
    client = res.get("client")
    db_select = await _get_db()
    db_insert = await _get_primary_db()

    
    is_available = await db_select.fetch_all(
    "SELECT * FROM callbacks WHERE client=:client",
    values={"client": client},
    )

    # if not registered add the client and callbackUrl to the DB
    if len(is_available) == 0:
        print("Registering")
        await db_insert.execute(
            "INSERT INTO callbacks(callbackUrl, client) VALUES(:callbackUrl, :client)",
            values={"callbackUrl": callbackUrl, "client":client}
            )
        return {
            "Success": "Client registered",
        }, 201  # should return correct answer?
    else:
        print("Already Registered")
        return {
            "Success": "Client already exists",
        }, 201  # should return correct answer?

# game
# 0 = id
# 1 = userId
# 2 = wordId
# 3 = guesses
# 4 = finished
# 5 = guess1
# 6 = guess2
# 7 = guess3
# 8 = guess4
# 9 = guess5
# 10 = guess6
