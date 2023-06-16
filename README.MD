# SVR Source Manager
Before reading further, make sure you are familiar with the main [SVR repository](https://github.com/TLMOS/security_video_retrieval).

## Overview
Source Manager is a client-side application that allows users to retrieve and send video data to SVR system.

Source Manager does not have user interface. After deployment, it should be registered in Search Engine. After that, users can have access to all of its functionality through Search Engine web interface.

Video data can be retrieved from the following sources:
- URL of a video or image file
- MJPEG stream
- Uploaded video or image file

## Deployment
Essential Source Manager configuration is stored in `.env` file. You can find full list of configuration variables in `common/config.py` file.

Before deploying Source Manager, you need to know URL of Search Engine instance.

After that, specify Search Engine URL in `.env` file.

After that, you can deploy Source Manager using docker-compose:
```bash
docker-compose up --build -d
```