# Pose Estimation and Analysis for Powerlifting

## Notice
```
********************************************************************************
*    Pose Estimation and Analysis for Powerlifting                             *
*    Final year dissertation project                                           *
*    Kyle Moir <katm2000@hw.ac.uk>                                             *
*    2023-2024                                                                 *
*                                                                              *
*    NEITHER THIS APPLICATION NOR ITS DEVELOPERS ARE LIABALE FOR ANY INJURY    *
*    CAUSED AS A RESULT OF THIS PROGRAM.                                       *
*                                                                              *
*    Always take care when practicing powerlifting.                            *
********************************************************************************
```

This project uses Mediapipe BlazePose human pose estimation to analyse the barbell squat and deadlift powerlifts. Bench press has been excluded due to the practical challenges faced when using a 2D camera to capture footage (obstructed joints).

## Usage
### Dependencies
- Ubuntu 20.04 or later is recommended.
- Python 3 with PIP

#### Install required packages
The required packages can be installed via:
`pip3 install -r requirements.txt`

### Running
The program runs from the command line:
`python3 program.py`

### Program Arguments
    - `--help`
    Print (this) help message

    - `--credits`
    Print software credits

    - `--input | -i <filepath>`
    Video file input

    - `--movement | -m <squat/deadlift>`
    Override movement detection

    - `--verbose | -v`
    Print more verbose info

    - `--dry`
    Dry run. Estimate pose and don't do any evaluation.


## Guide
The program should be provided with an mp4 video file containing footage of either a barbell squat or deadlift. Ideally the video has the subject fully in frame against a contrasting background. The program is tailored to evaluating a single rep, though some of the on-screen metrics will continue to be reported after a single rep is finished.

Example input data is provided in the [input data](input_data) folder.

The exercise will be automatically identified by the program. If you have trouble with this, try the `--movement <squat/deadlift` argument to override this automatic identification.

Analysing a video typically processes at half real time, ideally input videos are around 10 seconds or less.

### Output
When finished, the program will print to the console a list of metrics gathered, and a file `name_output.mp4` (from the input `name.mp4`).

