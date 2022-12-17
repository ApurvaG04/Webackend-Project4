auth: hypercorn auth --reload --debug --bind auth.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG

primary: ./bin/litefs -config ./etc/primary.yml
secondary_1: ./bin/litefs -config ./etc/secondary_1.yml
secondary_2: ./bin/litefs -config ./etc/secondary_2.yml

leaderboard: hypercorn leaderboard --reload --debug --bind leaderboard.local.gd:$PORT --access-logfile - --error-logfile - --log-level DEBUG
worker: rq worker --with-scheduler --verbose