# HackerOneParse
## Description
This is script needed for notify newest available bounty programs on HackerOne.
It is easier to search for vulnerabilities in new services, and therefore this script is useful for novice bounty hunters.
 - can send notify via telegram bot
## Launch
To run this script, you need to follow these steps:
#### for Linux
1. make sure that you have installed 3.x.x `Python` version, and `pip`.
1. execute command `sudo pip3 install Progress`
3. put the `hackeroneparse.py` script in the desired directory.
4. Run script via `python3 /your_directory/hackeroneparse.py` now `config.ini` file has been created.

#### for Windows
1. make sure that you have installed 3.x.x `Python` version, and `pip`.
1. execute command `pip install Progress` in `cmd`.
3. put the `hackeroneparse.py` script in the desired directory.
4. Run script via `python /your_directory/hackeroneparse.py` in `cmd`, now ```config.ini``` file has been created.

### Script can work in console mode, but if you want receive notifications to you telegram, follow steps:
1. need create TelegramBot following this instruction --> https://sendpulse.com/knowledge-base/chatbot/create-telegram-chatbot
3. in `config.ini` file must be write:
  ```
[Mode]
telegram = true                      <----this activate notification mode

[TelegramBot]
api_token = 559643:AA-EKLx-j1J       <----you telegram bot token 
chat_id =                            <----do not fill in yet
```
4. send a message to your bot in Telegram app.
5. Run script second time, it will offer the required ```chat_id``` number.
6. now fill your `chat_id =` in `config.ini` file.
7. Run script.
### To do round-the-clock scanning:
#### for Linux
1. put the `hackeroneparse.service` file in `/etc/systemd/system/` directory.
2. change directory on `ExecStart=` line in `hackeroneparse.service` file, it should look like this:

 `ExecStart=/usr/bin/python3 /your_directory/hackeroneparse.py`
 
3. Exec command `sudo systemctl daemon-reload` for reload services.
4. Exec `systemctl start hackeroneparse` for start hackeroneparse service.
5. You will receive message like a `HackerOneParse was started` in your Telegram app.

#### That is all! Service has been started and now is working
- also you can check current status via `systemctl status hackeroneparse` command.
- if you need stop the service, use `systemctl stop hackeroneparse` command.
