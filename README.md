# ViewPICam

A web user interface to monitor camera of raspberry pi

RPi Cam Web Interface is a web interface for the Raspberry Pi Camera module. It can be used for a wide variety of applications including surveillance, dvr recording and time lapse photography. It is highly configurable and can be extended with the use of macro scripts. It can be opened on any browser (smartphones included) and contains the following features:

    - View, stop and restart a live-preview with low latency and high framerate. Full sensor area available.
    - Control camera settings like brightness, contrast, ... live
    - Record full-hd videos and save them on the sd-card packed into mp4 container while the live-preview continues
    - Do timed or continuous video recording with splitting into fixed length segments
    - Take single or multiple (timelapse) full-res pictures and save them on the sd-card (live-preview holds on for a short moment)
    - Preview, download and delete the saved videos and pictures, zip-download for multiple files
    - Trigger captures by motion detection using internal or external detection processes.
    - Trigger captures by many scheduling-possibilities
    - Circular buffer to capture actions leading up to motion detection
    - Control Pan-Tilt or Pi-Light
    - Shutdown/Reboot your Pi from the web interface
    - Show annotations (eg timestamp) on live-preview and taken images/videos
    - Supports selection from 2 cameras when used with a compute module

**IMPORTANT NOTE**: This is for the Raspberry Pi camera only. It does NOT support USB cameras. 

For Raspberry Pi Zero W, 1, 2, 3, 4

## Settings

(***mandatory to access camera***)

**privileged** option enable, **vchiq** and **vcsm** device from host, must mount to container

`docker run -d --privileged -p 80:8000 -v /dev/vchiq:/dev/vchiq -v /dev/vcsm:/dev/vcsm ghcr.io/cyr-ius/viewpi-cam:latest`

## Folders

- /app/media -> screenshot and videos files
- /app/h264 -> temporary videos files before encoding
- /app/macros -> macros files
- /app/system -> settings files

`docker run -d --privileged -p 80:8000 -v /dev/vchiq:/dev/vchiq -v /dev/vcsm:/dev/vcsm -v /home/data/media:/app/media -v /home/data/system:/app/system -v /tmp:/app/h264 ghcr.io/cyr-ius/viewpi-cam:latest`


## Using docker compose

You can take a look at this example of [docker-compose.yml](https://raw.githubusercontent.com/cyr-ius/viewpi-cam/main/docker-compose.yml). Please adjust volume mount points to work with your setup. Then run it like below:

```
docker-compose up
```

## Environment Variables

Set the `SECRET_KEY` environment variable to a random value. This variable allows session and password encryption

Set the `SVC_SCHEDULER` environment variable to start scheduler at system startup (default: 1) [0|1]

Set the `SVC_RASPIMJPEG` environment variable to start raspimjpeg at system startup (default: 1)[0|1]

Set `LOG_LELVEL` to increase verbose: [INFO|WARNING|ERROR|DEBUG]

`docker run -d --privileged -p 80:8000 -e SECRET_KEY=01234567890 -v /dev/vchiq:/dev/vchiq -v /dev/vcsm:/dev/vcsm -v /home/data/media:/app/media -v /home/data/system:/app/system -/tmp:/app/h264 ghcr.io/cyr-ius/viewpi-cam:latest`

## License

MIT. See [License](https://github.com/cyr-ius/viewpicam/blob/master/LICENSE).

# Build

docker buildx build --platform=linux/arm/v6,linux/arm/v7 -t cyr-ius/viewpicam:latest . --load

# Test

docker run --rm -t viewpicam/armel:latest $(uname -m)
