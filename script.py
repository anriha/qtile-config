from libqtile.command.client import InteractiveCommandClient
c = InteractiveCommandClient()
print(c.screen.info()["index"])
