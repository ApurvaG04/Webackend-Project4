### Web Backend Project 4

| Group 9         |
| --------------- |
| Apurva Gawande|885897918|apurva.gawande@csu.fullerton.edu
| Hardik Vagrecha|885198390|hardik.vagrecha@csu.fullerton.edu
| Apeksha Shah|
| Maria Ortega|

##### HOW TO RUN THE PROJECT

1. Copy the contents of our [nginx config file](https://github.com/himanitawade/Web-Back-End-Project2/blob/master/nginxconfig.txt) into a new file within `/etc/nginx/sites-enabled` called `nginxconfig`. Assuming the nginx service is already running, restart the service using `sudo service nginx restart`.

Nginx Config:

```
server {
    listen 80;
    listen [::]:80;

    server_name tuffix-vm;

    location /registration {
        proxy_pass http://127.0.0.1:5000/registration;
    }

    location /newgame {
        auth_request /auth;
        proxy_pass http://gameservice;
    }

    location /addguess {
            auth_request /auth;
            proxy_pass http://gameservice;
    }

    location /allgames {
            auth_request /auth;
            proxy_pass http://gameservice;
    }

    location /onegame {
        auth_request /auth;
        proxy_pass http://gameservice;
    }


    location = /auth {
           internal;
           proxy_pass http://127.0.0.1:5000/login;
    }

}

upstream gameservice {
    server 127.0.0.1:5100;
    server 127.0.0.1:5101;
    server 127.0.0.1:5102;
    server 127.0.0.1:5103;
}
```

2. Initialize the databases within the project folder
   ```c
      // step 1. give the script permissions to execute
      chmod +x ./bin/start.sh

      // step 2. run the script
      ./bin/start.sh

      foreman start

   ```c
      // step 3. give the script permissions to execute
      chmod +x ./bin/init.sh

      // step 4. run the script
      ./bin/init.sh
   ```

3. Populate the word databases

   ```c
      python3 dbpop.py
   ```

4. Start the API

   ```c
      foreman start --formation user=1,game=3
      // NOTE: if there's an error upon running this where it doesn't recognize hypercorn, log out of Ubuntu and log back in.
   ```

5. Test all the endpoints using httpie
   - user
      - register account: `http POST http://tuffix-vm/registration username="yourusername" password="yourpassword"`
    
       Sample Output:
       ```
      {
         "id": 3,
         "password": "tawade",
         "username": "himani"
      }
      ```
     - login {Not accesible}: 'http --auth himani:tawade GET http://tuffix-vm/login'
     Sample Output:
     ```
      HTTP/1.1 404 Not Found
      Connection: keep-alive
      Content-Encoding: gzip
      Content-Type: text/html
      Date: Fri, 18 Nov 2022 21:04:31 GMT
      Server: nginx/1.18.0 (Ubuntu)
      Transfer-Encoding: chunked

      <html>
      <head><title>404 Not Found</title></head>
      <body>
      <center><h1>404 Not Found</h1></center>
      <hr><center>nginx/1.18.0 (Ubuntu)</center>
      </body>
      </html>
      ```
   - game

      - create a new game: `http --auth yourusername:yourpassword POST http://tuffix-vm/newgame`
      
      Sample Output:
      ```
      'http --auth himani:tawade POST http://tuffix-vm/newgame'
      {
         "answerid": 3912,
         "gameid": "b0039f36-6784-11ed-ba4a-615e339a8400",
         "username": "himani"
      }
      ```
      Note - this will return a `gameid`
    - add a guess: `http --auth yourusername:yourpassword PUT http://tuffix-vm/addguess gameid="gameid" word="yourguess"`

    Sample Output:
    ```
      http --auth himani:tawade PUT http://tuffix-vm/addguess gameid="b0039f36-6784-11ed-ba4a-615e339a8400" word="amigo"
     {
        "Accuracy": "XXOOO",
        "guessedWord": "amigo"
     }
     ```
    - display your active games: `http --auth yourusername:yourpassword GET http://tuffix-vm/allgames`

    Sample Output:
    ```
      http --auth himani:tawade GET http://tuffix-vm/allgames
      [
         {
            "gameid": "b0039f36-6784-11ed-ba4a-615e339a8400",
            "gstate": "In-progress",
            "guesses": 1
         }
      ]
      ```
    - display the game status and stats for one game: `http --auth yourusername:yourpassword GET http://tuffix-vm/onegame?id=gameid`
       - example: `.../onegame?id=b97fcbb0-6717-11ed-8689-e9ba279d21b6`
    Sample Output:
    ```
      http --auth himani:tawade GET http://tuffix-vm/onegame?id="b0039f36-6784-11ed-ba4a-615e339a8400"
      [
         {
             "gameid": "b0039f36-6784-11ed-ba4a-615e339a8400",
            "gstate": "In-progress",
            "guesses": 1
          },
          {
             "accuracy": "XXOOO",
             "guessedword": "amigo"
          }
      ]
      ```
