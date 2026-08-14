import docker

client = docker.from_env()

info = client.info()

container = client.containers.get('test')

for event in client.events(decode=True):
    if event["Action"] == "die":
        print(f"{event["Actor"]["Attributes"]["name"]} died with code {event["Actor"]["Attributes"]["exitCode"]}")