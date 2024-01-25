from raspc_notif import notif
from time import sleep
import subprocess


#Enter the User API Key you find in the RaspController app
sender = notif.Sender(apikey = "PHskh9jdhjWtHdYICbOGEruhPOC2-ImyEhsgoCgtQkC__08H0EmDz4lRVB7B1J1RjW1VHR_U_")



notif_message = "Démarrage Dada"
notification = notif.Notification("Attention!", notif_message, high_priority = True)
result = sender.send_notification(notification)

#Check if the submission was successful
if result.status == notif.Result.SUCCESS:
    print(result.message)
else:
    print("ERROR: {0}".format(result.message))