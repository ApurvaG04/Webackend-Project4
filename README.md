# CPSC-449-Web Backend Engineering:Project-4
# Project Members:

1. Apurva Umakant Gawande
2. Hardik Vagrecha            | 885198390 | hardik.vagrecha@csu.fullerton.edu
3. Gowtham Kishore Mahadasu | 885194209 | Mgk9061@csu.fullerton.edu
4. Sravani Kallempudi       | 885332171 | sravanik@csu.fullerton.edu

# Project description: 

In this project, we are creating three replicas of the database which are named primary, secondary 1 and secondary 2. We are then configuring our game service such that the reads are distributed across the three replicas while writes continue to go to the primary database. We have created a new RESTful microservice to maintain a leaderboard for Wordle games.

# Configuration files:
1. Procfile is a mechanism for declaring what commands are run by your application to start the app 
2. Update the nginx.config from nginx_config/tutorial into default file present in /etc/nginx/sites-enabled 

# The following are the steps to run the project:
1. Installing and configuring Nginx:
```bash
sudo apt update
sudo apt install --yes nginx-extras
```
2. Then cd into the CPSC449-Project3 folder and run the following commands:
```bash
cd bin
chmod u+x litefs
sh init_dir.sh
cd ..
```
3. Start the services
```bash
foreman start 
```
4. Run both the init scripts to populate the database and automatically connect the api to the database. 
```bash
open a new terminal at the project folder and enter:
sh ./bin/init_auth.sh
sh ./bin/init_game.sh
```
Now the API can be run using Postman(the method which we followed) or using curl or httpie.

## ENDPOINT 1:
For registering an user: @app.route("/register", methods=["POST"])
```bash
http POST http://tuffix-vm/register/ username=Rain password=rain@123
```
## ENDPOINT 2:
For authenticating the user:@app.route("/auth", methods=["GET"])
```bash
Ex: On postman with Basic-Auth: http://tuffix-vm/auth
note: this is no longer available externally, but other endpoints will make use of it
```
## ENDPOINT 3: 
For creating a new game for an authenticated user:@app.route("/game/", methods=["POST"])
```bash
Ex: On postman with Basic-Auth: http://tuffix-vm/game
http --auth Rain:rain@123 POST tuffix-vm/game
```
## ENDPOINT 4:
For getting the game state of the authenticated user:@app.route("/game/:gameId", methods=["GET"])
```bash
Ex: On postman with Basic-Auth: http://tuffix-vm/game/:gameId
http --auth Rain:rain@123 GET tuffix-vm/game/b96f966d-f76a-4d0e-9909-ea3f5823727b
``` 
## ENDPOINT 5:
List all the games for the authenticated user:@app.route("/my-games", methods=["GET"])
```bash
Ex: On postman with Basic-Auth: http://tuffix-vm/my-games
http --auth Rain:rain@123 GET tuffix-vm/my-games
```
## ENDPOINT 6:
Guessing a word: @app.route("/game/:gameId", methods=["PATCH"])
```bash
Ex: On postman with Basic-Auth: http://tuffix-vm/game/:gameId
note: In the body, select raw - JSON and then {"word":"apple"}

http --auth aaaa:rain@123 PATCH tuffix-vm/game/b96f966d-f76a-4d0e-9909-ea3f5823727b word=money
```
## ENDPOINT 7:
Reporting a game to the leaderboard: @app.route("/reportgame", methods=["POST"])
```bash
Ex: On postman: http://127.0.0.1:5400/reportgame
note: In the body, select raw - JSON and then {"username":"Rain", "result":1, "guesses":3}
note2: result is a 1 for win and 0 for loss

http --auth POST http://127.0.0.1:5400/reportgame username=Rain result=1 guesses=3
```
## ENDPOINT 8:
Resetting the leaderboard to empty: @app.route("/resetleaderboard", methods=["POST"])
```bash
Ex: On postman: http://127.0.0.1:5400/resetleaderboard
http POST http://127.0.0.1:5400/resetleaderboard
```
## ENDPOINT 9:
Viewing the top 10 on the leaderboard: @app.route("/leaderboard", methods=["GET"])
```bash
Ex: On postman: http://tuffix-vm/leaderboard
# http GET http://tuffix-vm/leaderboard

http http://127.0.0.1:5400/leaderboard
```
