import sys
import cv2
import time
import math
import numpy as np
import mediapipe as mp

video_input = ''
movement_override = False
movement = ''
debug = False
dry_run = False
begin_lift = -1

def notice():
    print('''
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
    ''')

def credits():
    print('''
Open source libraries used:
    OpenCV      (cv2)
    MediaPipe   (mediapipe)
    NumPy       (numpy)

Authors:
    Kyle Moir   <katm2000@hw.ac.uk>
    ''')

def render_text(frame, text, coords, fg_colour=(0, 255, 0)):
    bg_colour = (0, 0, 0)
    fg_thickness = 3
    bg_thickness = 6
    
    cv2.putText(frame, text, coords, cv2.FONT_HERSHEY_SIMPLEX, 1.5, bg_colour, bg_thickness, cv2.LINE_AA)
    cv2.putText(frame, text, coords, cv2.FONT_HERSHEY_SIMPLEX, 1.5, fg_colour, fg_thickness, cv2.LINE_AA)

def progress_bar(iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '#', printEnd = "\r"):
    # https://stackoverflow.com/questions/3173320/text-progress-bar-in-terminal-with-block-characters
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)

    rad = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    deg = np.abs(rad*180.0/np.pi)

    if deg > 180.0:
        deg = 360-deg

    return deg 

def colour_scale(percentage):
    pct_diff = 1.0 - percentage
    red = min(255, pct_diff*2 * 255)
    green = min(255, percentage*2 * 255)

    return (0, red, green)

def main():
    global video_input
    if video_input == '':
        return
    video_capture = cv2.VideoCapture(video_input)

    global debug

    frames_processed = 0
    start = int(time.time())

    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()

    global movement_override
    global movement

    global begin_lift

    print('Analysing video input: ', video_input)

    fourcc = cv2.VideoWriter_fourcc(*'MP4V')
    output_destination = video_input.split('.')[0] + '_output.mp4'
    fps = video_capture.get(cv2.CAP_PROP_FPS)
    frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if (debug):
        print('Input FPS is:', fps)
    video_output = cv2.VideoWriter(output_destination, fourcc, fps, (int(video_capture.get(3)), int(video_capture.get(4))))

    lift_start = -1
    metrics = [-1, -1, -1, -1, -1]

    last_world_landmarks = None
    bar_drop = 0
    apex = 999

    while video_capture.isOpened():
        progress_bar(frames_processed, frame_count, prefix = 'Progress:', suffix = 'Complete', length = 50)

        ret, frame = video_capture.read()
        
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = pose.process(frame_rgb)

        # get the pose estimation data for analysis
        try:
            landmarks = results.pose_landmarks.landmark
            world_landmarks = results.pose_world_landmarks.landmark
        except Exception as e:
            print('Warning: Pose estimation failed for frame', frames_processed)
            continue

        if landmarks:
            if dry_run == False:
                if movement_override == False:
                    # try to detect movement
                    # if wrist is above hip, it's likely we have a squat movement
                    if world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y < world_landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y:
                        movement = 'squat'
                    # otherwise we presume it's a deadlift movement
                    else:
                        movement = 'deadlift'
                
                if movement == 'squat':
                    # average depth between hips
                    depth = (world_landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y + world_landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].y) / 2
                    knee_balance = (world_landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x - world_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x) - (world_landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x - world_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x)

                    apex = min((world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y + world_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y) / 2, apex)

    #                render_text(frame, str(apex), (50, 500))
    #                render_text(frame, str((world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y + world_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y) / 2), (50, 550))

                    if last_world_landmarks:
                        if (world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y + world_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y) / 2 > apex:
                            if (world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y + world_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y) / 2 < (last_world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y + last_world_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y) / 2:
                                bar_drop += 1
                            else:
                                bar_drop = 0

                            render_text(frame, str(bar_drop), tuple(np.multiply([landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y], [video_capture.get(3), video_capture.get(4)]).astype(int)))

                            # if the bar drops for 1s or more
                            if bar_drop >= fps:
                                render_text(frame, 'Is bar dropping?', tuple(np.multiply([landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y], [video_capture.get(3), video_capture.get(4)]).astype(int)))

                    if metrics[0] == -1:
                        metrics[0] = 999
                    else:
                        # min because world space coords
                        metrics[0] = min(depth, metrics[0])

                    # max because screen space coords
                    metrics[1] = max(knee_balance, metrics[1])

                    if landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y <= landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y and landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y <= landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y:
                        metrics[3] = max(metrics[2], True)

                    l_hip       = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    l_knee      = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    l_ankle     = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                    l_shoulder  = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]

                    leg_ang = angle(l_hip, l_knee, l_ankle)
                    lat_ang = angle(l_shoulder, l_hip, l_knee)

                    render_text(frame, str(leg_ang), tuple(np.multiply(l_knee, [video_capture.get(3), video_capture.get(4)]).astype(int)), fg_colour=colour_scale(leg_ang/180))
                    render_text(frame, str(lat_ang), tuple(np.multiply(l_hip, [video_capture.get(3), video_capture.get(4)]).astype(int)), fg_colour=colour_scale(lat_ang/180))


                    if begin_lift == -1:
                        if lat_ang < 165:
                            begin_lift = frames_processed
                    elif metrics[2] == -1:
                        if lat_ang >= 165:
                            metrics[2] = (frames_processed - begin_lift) / fps

                    time_txt = -1
                    if begin_lift == -1:
                        time_txt = '0'
                    elif metrics[2] == -1:
                        time_txt = str(round((frames_processed - begin_lift) / fps, 3))
                    else:
                        time_txt = str(round(metrics[2], 3))

                    render_text(frame, 'movement: barbell squat', (0, 50))
                    render_text(frame, 'depth (m): ' + str(round(depth, 2)) + ', ' + str(round(metrics[0], 2)), (0, 50*2))
                    render_text(frame, 'knee balance: ' + str(round(knee_balance, 2)), (0, 50*3))
                    render_text(frame, 'time (s): ' + time_txt, (0, 50*4))

                elif movement == 'deadlift':
                    l_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value]
                    r_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value]
                    l_knee  = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value]
                    r_knee  = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value]
                    l_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
                    r_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]

                    l_shin = (l_ankle.y + l_knee.y) / 2
                    r_shin = (r_ankle.y + r_knee.y) / 2

                    if l_wrist.visibility > 0.8 and r_wrist.visibility > 0.8 and l_knee.visibility > 0.8 and r_knee.visibility > 0.8:
                        if (l_wrist.y - l_knee.y < 0 and r_wrist.y - r_knee.y < 0):
                            metrics[0] = max(True, metrics[0])

                        if begin_lift == -1:
                            if r_wrist.y < r_shin and l_wrist.y < l_shin:
                                begin_lift = frames_processed
                        elif metrics[2] == -1:
                            if r_wrist.y > r_shin and l_wrist.y > l_shin:
                                metrics[2] = (frames_processed - begin_lift) / fps

                    apex = max((world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y + world_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y) / 2, apex)

                    if last_world_landmarks:
                        if (world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y + world_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y) / 2 < (last_world_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y + last_world_landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y) / 2:
                            bar_drop += 1
                        else:
                            bar_drop = 0

                        render_text(frame, str(bar_drop), tuple(np.multiply([landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y], [video_capture.get(3), video_capture.get(4)]).astype(int)))

                        # if the bar drops for .1s or more
                        if bar_drop >= fps/10:
                            render_text(frame, 'Is bar dropping?', tuple(np.multiply([landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y], [video_capture.get(3), video_capture.get(4)]).astype(int)))
                            metrics[1] += 1

                    time_txt = -1
                    if begin_lift == -1:
                        time_txt = '0'
                    elif metrics[2] == -1:
                        time_txt = str(round((frames_processed - begin_lift) / fps, 3))
                    else:
                        time_txt = str(round(metrics[2], 3))

                    render_text(frame, 'movement: deadlift', (0, 50))
                    render_text(frame, 'time (s): ' + time_txt, (0, 50*2))

                    #render_text(frame, str(l_wrist.y), (0, 50*3))
                    #render_text(frame, str(l_knee.y), (0, 50*4))
                    #render_text(frame, str(l_ankle.y), (0, 50*5))
                    #render_text(frame, str(l_shin), (0, 50*6))

        if results.pose_landmarks:
            # draw landmarks (points and lines)
            mp_drawing = mp.solutions.drawing_utils
            mp_drawing.draw_landmarks(frame,results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                        mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2, circle_radius=2), 
                                        mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2))               

        # add frame to the video being created
        video_output.write(frame)
        frames_processed += 1

        last_world_landmarks = world_landmarks

        # uncomment to see frames as they are rendered
        # cv2.imshow('Pose Estimation', frame)

    # cleanup
    video_capture.release()
    video_output.release()
    cv2.destroyAllWindows()
   
    if debug:
        print('Finished processing', frames_processed, 'frames in', int(time.time())-start, 's!')
  
    output(metrics)

def squat_output(metrics):
    '''
    Squat Metrics
      0 - Depth
      1 - Knee collapse
      2 - Time
      3 - Hips below knees
    '''

    print('\nSquat depth (m):', round(metrics[0], 2))
    print('Worst knee balance:', round(metrics[1], 2))
    print('Time (s):', round(metrics[2], 2))
    print('Hips below knees:', metrics[3])

def deadlift_output(metrics):
    '''
    Deadlift Metrics
      0 - Complete Lift
      1 - Downwards movement (before apex)
      2 - Time
    '''

    print('\nComplete lift:', metrics[0])
    print('Doward movement:', metrics[1])
    print('Time (s):', round(metrics[2], 2))

def output(metrics):
    print('\n--------------------------------------------------------------------------------')

    global movement

    if movement == 'squat':
        squat_output(metrics)
    elif movement == 'deadlift':
        deadlift_output(metrics)

    print('\n--------------------------------------------------------------------------------')

def cli():
    if '--help' in sys.argv or len(sys.argv) < 2:
        print('''
COMMANDS
    --help
    Print this message

    --credits
    Print software credits

    --input | -i <filepath>
    Video file input

    --movement | -m <squat/deadlift>
    Override movement detection

    --verbose | -v
    Print more verbose info

    --dry
    Dry run. Estimate pose and don't do any evaluation.
        ''')
        sys.exit()

    if '--credits' in sys.argv:
        credits()
        sys.exit()

    global video_input
    if '--input' in sys.argv:
        video_input = sys.argv[sys.argv.index('--input')+1]
    elif '-i' in sys.argv:
        video_input = sys.argv[sys.argv.index('-i')+1]
    else:
        print('Warning: No video input was provided.')

    global movement
    global movement_override
    if '--movement' in sys.argv:
        movement_override = True
        movement = sys.argv[sys.argv.index('--movement')+1]
    elif '-m' in sys.argv:
        movement_override = True
        movement = sys.argv[sys.argv.index('-m')+1]

    global debug
    if '--verbose' in sys.argv:
        debug = True
    elif '-v' in sys.argv:
        debug = True

    global dry_run
    if '--dry' in sys.argv:
        dry_run = True

    main()

if __name__ == '__main__':
    notice()
    cli()
