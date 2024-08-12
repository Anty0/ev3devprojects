# EV3dev Projects

This project represents a culmination of all the projects I've done with the EV3 Lego Mindstorms. After I've done some projects in lejos, event tryied connecting the EV3 to an Android device, then followed by some projects in ev3dev, I've decided to undertake a project where I wanted to create an ultimate base for all my projects.

The project serves as a baseline where one can define a model of a robot, by defining positions of all wheels, sensors, and motors and their relationships. Implementations of a `Pilot` and other classes are then capable of using this model to perform various tasks while the code itself doesn't need to take the specifics of the robot into account.

On top of that, there is a full fledged simulator mode and whole program can be controlled remotely from a web page through a REST API. (Note: the EV3 brick unfortunately is so slow at request handling, it slows down a cycle of running program significantly - this for example makes line following unstable defeating the purpose of the web interface for dynamic configuration of the regulator a bit.)

I've reimplemented some of the projects using this interface:

- Auto Drive
- Beacon Follow
- Line Follow

## Requirements

You'll need to install the ev3dev OS on your EV3 brick. You can find the instructions on the [ev3dev website](https://www.ev3dev.org/docs/getting-started/).

## Usage

To run the program, simply execute the `main.py` script. You need to setup the `hardware.py` file to match your robot configuration though.

The program will start a web server on the EV3 brick, which you can access from your computer by navigating to the IP address of the brick on port 8000. You can then control the robot remotely.

You can also run the program in simulator mode by executing the `main.py` script with the `--simulate` flag.
