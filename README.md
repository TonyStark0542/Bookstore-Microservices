# Bookstore-Microservices

Steps:
1. ensure docker is installed and gemini api key is present in the local env machine
2. run below command:
docker compose up -d --build
docker exec -it mongodb-backend mongorestore --archive=/backup/db_backup.archive --gzip
3. to stop use below command:
docker compose down
