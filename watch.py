import docker
import evidence
import diagnose

client = docker.from_env()

for event in client.events(decode=True):
    if event["Action"] == "die":
        name = event["Actor"]["Attributes"]["name"]
        code = event["Actor"]["Attributes"]["exitCode"]
        path = evidence.collect(client, event)
        print(f"{name} died with code {code} -> {path}")
        print("Diagnosing with claude")

        try:
            result = diagnose.diagnostic_prompt(path)
            print(diagnose.format_diagnosis(result))
        except:
            print(f"  diagnosis failed: {e}")
        