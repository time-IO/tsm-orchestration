# Configure Mosquitto mqtt broker user authentication

SOURCE :
- https://git.ufz.de/rdm-software/timeseries-management/mqtt-dataingest/-/tree/master/mosquitto
 
```
username: testUser
password: password
```

To add more users to the password file, or to change the password for an existing user:
`mosquitto_passwd /mosquitto/config/mosquitto.passwd <username>`

To remove a user from a password file:
`mosquitto_passwd -D  /mosquitto/config/mosquitto.passwd <username>`

## Infos

- https://mosquitto.org/documentation/authentication-methods/
- https://github.com/iegomez/mosquitto-go-auth
