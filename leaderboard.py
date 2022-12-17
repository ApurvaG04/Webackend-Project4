from quart import Quart, g, request, jsonify, abort
from quart_schema import validate_request, RequestSchemaValidationError, QuartSchema
import toml
import redis
import json
import httpx
import time
import socket
app = Quart(__name__)
QuartSchema(app)

r = redis.Redis(host='localhost', port=6379, db=0, charset='utf-8', decode_responses=True)
r.flushall

@app.errorhandler(400)
def badRequest(e):
    return {"error": str(e).split(':', 1)[1][1:]}, 400

# ---------------REPORT A GAME---------------

# before serving client establish connection with games service
# https://www.python-httpx.org/exceptions/

try:
    response = httpx.post('http://127.0.0.1:5100/webhook', json={'callbackUrl': 'http://127.0.0.1:5400/reportgame', 'client': 'leaderboard'})
except httpx.RequestError:
    time.sleep(5)

@app.route("/reportgame", methods=["POST"])
async def addScore():
    body = await request.get_json()
    username = body.get("username")
    result = body.get("result")
    guesses = body.get("guesses")

    if r.hexists(username, "total") == False:
        r.hmset(username, {"total":0, "count":0})
    if (result == 1):
        score = (7 - guesses)
    else:
        score =  0
    total = r.hincrby(username, "total", score)
    count = r.hincrby(username, "count", 1)
    average = total/count

    r.zadd("leaderboard", {username:average})
    return {"message": "game successfully reported", "updated_average": average},200


# ---------------GET LEADERBOARD TOP 10---------------

@app.route("/leaderboard", methods=["GET"])
async def getTopTen():
    lb = r.zrange("leaderboard", 0, 9, withscores=True, desc=True)
    lbdict = dict((i[0],i[1]) for i in lb)
    print(lbdict)
    return lbdict,200


# ---------------RESET LEADERBOARD DATABASES---------------

@app.route("/resetleaderboard", methods=["POST"])
async def clearLeaderboard():
    r.flushall()
    return {"message": "leaderboard reset"},200