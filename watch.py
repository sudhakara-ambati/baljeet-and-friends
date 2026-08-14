import docker
import evidence

client = docker.from_env()

for event in client.events(decode=True):
    if event["Action"] == "die":
        name = event["Actor"]["Attributes"]["name"]
        code = event["Actor"]["Attributes"]["exitCode"]
        path = evidence.collect(client, event)
        print(f"{name} died with code {code} -> {path}")