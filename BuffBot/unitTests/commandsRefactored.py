"""
Logic for the following commands will be overrided to perform unit tests on the logic in the different commands.
Overriding in this file means replacing bot.say("x") with return statements.
Moreover, the logic in these functions will neither require an instance of a bot nor a client.

"""
import hashlib

from aiohttp import ClientSession
from simpleeval import simple_eval
import math
from BuffBot.commands import get_random_line


class Commands:
    def __init__(self):
        self.owners = ["85431603408420864", "235892294857916417", "269919583899484160", "95596654194855936",
                       "125307006260084736", "209397846959456256"]
        self.validMsgs = ["!bye", "!math", "!8ball", "!whoIsTheBuffest", "!flagChan", "!smugAdd", "!smug", "!patrol"]

    # Check if the client requesting is an owner and wheter the msg is valid or not.
    def checkOwnerAndMsg(self, msg, clientID):
        if clientID not in self.owners:
            return print(clientID + "is not an owner of the bot.")
        if msg not in self.validMsgs:
            return print(msg + " is not a valid message.")

    # TODO: Remove the print statements, and simply return the strings.

    def bye(self, msg, clientID):
        self.checkOwnerAndMsg(msg, clientID)
        if clientID in self.owners and msg in self.validMsgs:
            return "Bye bye!"

    def math(self, msg, clientID, *, params):
        self.checkOwnerAndMsg(msg, clientID)
        try:
            result = simple_eval("{}".format(params), names={"e": math.e, "pi": math.pi},
                                 functions={"log": math.log, "sqrt": math.sqrt, "cos": math.cos, "sin": math.sin,
                                            "tan": math.tan})
            return result
        except Exception:
            result = "Read the fucking manual"
            return result

    def eightBall(self, msg, clientID):
        self.checkOwnerAndMsg(msg, clientID)
        return get_random_line('8ballresponses.txt')


    def whoIsTheBuffest(self, msg, clientID):
        self.checkOwnerAndMsg(msg, clientID)
        return "Wiklem"

    def smugAdd(self, path):
        allowed_content = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/gif': 'gif'}
        with ClientSession().get(path) as r:
            if r.status == 200:
                file = r.content.read()
                type = r.headers['Content-Type']
            if type not in allowed_content:
                print("Illegal filetype")
                return
            else:
                hash = hashlib.md5(file).hexdigest()
                filename = "smug-anime-faces/{}.{}".format(hash, allowed_content[type])
                with open(filename, 'wb') as f:
                    f.write(file)
                return f




"""
if __name__ == "__main__":
    obj = Commands()
    obj.bye("!bye", "85431603408420864")
    obj.math("!math", "85431603408420864", params=4 * 4)
"""
