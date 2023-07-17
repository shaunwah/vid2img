import decimal
import os
import sys

from tqdm import tqdm
import cv2
import numpy

output_count = 0
output_error_count = 0


def process_batch(args):
    input_path = args.input
    input_sorted = args.sorted
    output_path = args.output
    output_rows = args.rows
    output_columns = args.columns
    output_delay_in_seconds = args.delay
    output_offset_in_seconds = args.offset
    output_resize = args.resize
    output_limit = args.limit

    if output_rows <= 0 or output_columns <= 0 or output_delay_in_seconds < 0 or output_offset_in_seconds < 0\
            or output_resize <= 0:
        print(f"Non-negative and/or non-zero argument values required! Stopping everything.", file=sys.stderr)
        exit()

    if output_path is None:
        if os.path.isdir(input_path):
            args.output, output_path = input_path, input_path
        else:
            args.output, output_path = os.path.dirname(input_path), os.path.dirname(input_path)

    if not os.path.exists(input_path):
        print(f"{input_path} does not exist! Stopping everything.", file=sys.stderr)
        exit()

    try:
        if not os.path.exists(output_path):
            os.mkdir(output_path)
    except OSError:
        print(f"Failed to create {output_path}! Stopping everything.", file=sys.stderr)
        exit()

    if os.path.isdir(input_path):
        files = os.listdir(input_path)
        if input_sorted:
            files = sorted(files)
        if output_limit <= 0:
            output_limit = len(files)
        for file in files:
            file = os.path.join(input_path, file)
            if output_count < output_limit and os.path.isfile(file):
                args.input = file
                process_single(args)
    else:
        process_single(args)

    print(f"Processed {output_count} file(s) with {output_error_count} error(s).")


def process_single(args):
    input_path = args.input
    output_path = args.output
    output_rows = args.rows
    output_columns = args.columns
    output_delay_in_seconds = args.delay
    output_offset_in_seconds = args.offset
    output_resize = args.resize
    output_override = args.override
    verbose_mode = args.verbose
    global output_count, output_error_count

    input_file = os.path.basename(input_path)
    input_file_name = os.path.splitext(input_file)[0]
    input_file_extension = os.path.splitext(input_file)[1]

    output_file_extension = ".jpg"
    output_file_name_extras = f"{output_rows}x{output_columns}-{decimal.Decimal(output_resize).normalize()}x"
    output_file_name = f"{input_file_name}-{output_file_name_extras}"
    output_file = f"{output_file_name}{output_file_extension}"
    output_path = f"{output_path}/{output_file}"

    output_image_count = int(output_rows * output_columns)

    if not input_file_extension == ".mp4":
        # print(f"{input_file} is not a valid file to process! Skipping...", file=sys.stderr)
        return

    if not output_override and os.path.exists(output_path):
        print(f"{output_path} already exists. Skipping...", file=sys.stderr)
        return

    cap = cv2.VideoCapture(input_path)
    cap_frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap_fps = int(cap.get(cv2.CAP_PROP_FPS))
    cap_delay_in_frames = int(output_delay_in_seconds * cap_fps)
    cap_offset_in_frames = int(output_offset_in_seconds * cap_fps)
    cap_step_frame = int(cap_frame_count // output_image_count)

    cap_max_tolerance = 0.05
    cap_max_offset_in_frames = int((cap_step_frame - (cap_step_frame % cap_fps)) * (1 - cap_max_tolerance))
    cap_max_offset_in_seconds = int(cap_max_offset_in_frames // cap_fps)
    cap_max_delay_in_frames = int(((cap_frame_count - (cap_frame_count % cap_fps)) - cap_max_offset_in_frames)
                                  * (1 - cap_max_tolerance))
    cap_max_delay_in_seconds = int(cap_max_delay_in_frames // cap_fps)

    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    output_height = output_rows * frame_height
    output_width = output_columns * frame_width

    output_generated_file = numpy.zeros((output_height, output_width, 3), numpy.uint8)

    print(f"Building and compiling thumbnails for {input_file}...")

    if verbose_mode:
        print(f"""\
input: {input_file}
output: {output_file}
rows: {output_rows}
columns: {output_columns}
image_count: {output_rows * output_columns}
frame_count: {cap_frame_count} frames
frame_step: {cap_step_frame} frames
frames_per_second: {cap_fps} fps
delay: {output_delay_in_seconds} seconds, {cap_delay_in_frames} frames
max_delay: {cap_max_delay_in_seconds} seconds, {cap_max_delay_in_frames} frames
max_delay_tolerance: {int(cap_max_tolerance * 100)}%
offset: {output_offset_in_seconds} seconds, {cap_offset_in_frames} frames
max_offset: {cap_max_offset_in_seconds} seconds, {cap_max_offset_in_frames} frames
max_offset_tolerance: {int(cap_max_tolerance * 100)}%
resize: {int(output_resize * 100)}%""")

    if output_delay_in_seconds > cap_max_delay_in_seconds:
        print(f"Delay exceeded file limit. Automatically set from {output_delay_in_seconds} to "
              f"{cap_max_delay_in_seconds} seconds.")
        cap_delay_in_frames = cap_max_delay_in_frames

    if output_offset_in_seconds > cap_max_offset_in_seconds:
        print(f"Offset exceeded file limit. Automatically set from {output_offset_in_seconds} to "
              f"{cap_max_offset_in_seconds} seconds.")
        cap_offset_in_frames = cap_max_offset_in_frames

    cap_starting_frame = 0 + (cap_delay_in_frames + cap_offset_in_frames)
    cap_current_frame = 0 + cap_offset_in_frames

    frame_count = 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, cap_starting_frame)
    for _ in tqdm(range(output_image_count)):
        ret, frame = cap.read()
        if cap_current_frame <= cap_frame_count:
            try:
                row = frame_count // output_columns
                column = frame_count % output_columns
                x = column * frame_width
                y = row * frame_height
                output_generated_file[y:y + frame_height, x:x + frame_width] = frame
                frame_count += 1
            except TypeError:
                pass
            cap_current_frame += cap_step_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, cap_current_frame)

    if frame_count < output_image_count:
        print(f"An issue occurred while building {output_image_count - frame_count} frame(s).",
              file=sys.stderr)
        output_error_count += 1

    if output_resize <= 1:
        try:
            output_resized_height = int(output_height * output_resize)
            output_resized_width = int(output_width * output_resize)
            output_generated_file = cv2.resize(output_generated_file, (output_resized_width, output_resized_height),
                                               interpolation=cv2.INTER_AREA)
        except AttributeError:
            print(f"An issue occurred while resizing.", file=sys.stderr)
            output_error_count += 1
    else:
        print("Resize values have to be less than 100%! Skipping resizing...", file=sys.stderr)

    try:
        cv2.imwrite(output_path, output_generated_file)
        output_count += 1
        print(f"Built and compiled thumbnails to {output_path}. [{output_count}]")

    except OSError:
        print(f"An issue occurred while saving to {output_file}.", file=sys.stderr)
        output_error_count += 1

    cap.release()
    cv2.destroyAllWindows()
