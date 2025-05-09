-- Set authentication plugin for root user
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY '${MYSQL_ROOT_PASSWORD}';
FLUSH PRIVILEGES;

-- Create user with native password authentication
CREATE USER IF NOT EXISTS 'msat'@'%' IDENTIFIED WITH mysql_native_password BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON msatdb.* TO 'msat'@'%';
FLUSH PRIVILEGES; 