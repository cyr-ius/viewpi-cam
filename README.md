# ViewPICam

A web user interface to monitor camera of raspberry pi

Default username and password are `admin`.

### Using docker compose

You can take a look at this example of [docker-compose.yml](https://github.com/Cyr-ius/viewpicam/tree/master/example). Please adjust volume mount points to work with your setup. Then run it like below:

```
docker-compose up
```

### Environment Variables


Set the `SESSION_SECRET` environment variable to a random value.

In order to sent the wireguard configuration to clients via email (using sendgrid api) set the following environment variables

```
USERNAME: your root account
PASSWORD: your password account
USER_MAIL: root's mail
SECURITY_TWO_FACTOR: [True|False] Enable Totp panel
SECURITY_CHANGEABLE:[True|False] Enable Change passdword panel
SECURITY_PASSWORD_LENGTH_MIN: Length password
SECURITY_RECOVERABLE:[True|False] Enable recoverable account (send mail)
SECURITY_REGISTERABLE:[True|False] Accept register account at login page (Strongly discouraged )
SECURITY_CONFIRMABLE:[True|False] Confirm account A valid email address is required for root account
```

## License
MIT. See [LICENSE](https://github.com/cyr-ius/viewpicam/blob/master/LICENSE).

# Build
docker buildx build -t viewpicam/amd64:latest . --load
docker buildx build --platform=linux/arm/v6 -t viewpicam/armel:latest . --load

# Test
docker run --rm -t viewpicam/armel:latest $(uname -m)