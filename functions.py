import os
import sys

from tqdm import tqdm
import cv2
import numpy

files_processed = 0


def vids2img(
        input_path,
        output_path,
        output_delay,
        output_offset,
        output_rows,
        output_columns,
        output_resize,
        output_override
):
    print(f"""\
OPTIONS:
    FILESYSTEM:
        input_path: {input_path}
        output_path: {output_path}
    THUMBNAILS:
        delay: {output_delay}
        offset: {output_offset}
        image_count: {output_rows * output_columns}
        rows: {output_rows}
        columns: {output_columns}
        resize: {output_resize}%
    """)

    if not os.path.exists(input_path):
        print(f"{input_path} does not exist!", file=sys.stderr)
        exit()

    try:
        if not os.path.exists(output_path):
            os.mkdir(output_path)
    except OSError:
        print(f"Failed to create {output_path}! Stopping everything.", file=sys.stderr)
        exit()

    if os.path.isdir(input_path):
        for file in os.listdir(input_path):
            file = os.path.join(input_path, file)
            if os.path.isfile(file):
                vid2img(
                    file,
                    output_path,
                    output_delay,
                    output_offset,
                    output_rows,
                    output_columns,
                    output_resize,
                    output_override
                )
    else:
        vid2img(
            input_path,
            output_path,
            output_delay,
            output_offset,
            output_rows,
            output_columns,
            output_resize,
            output_override
        )

    print(f"Built and compiled {files_processed} file(s).")


def vid2img(
        input_path,
        output_path,
        output_delay,
        output_offset,
        output_rows,
        output_columns,
        output_resize,
        output_override
):
    global files_processed
    input_file = os.path.basename(input_path)
    input_file_name = os.path.splitext(input_file)[0]
    input_file_extension = os.path.splitext(input_file)[1]

    output_file_name_extras = f"{output_delay}d{output_offset}o{output_resize}r-{output_rows}x{output_columns}"

    output_file = f"{input_file_name}-{output_file_name_extras}.jpg"
    output_path = f"{output_path}/{output_file}"

    if not input_file_extension == ".mp4":
        print(f"{input_file} is not a valid file to process! Skipping...", file=sys.stderr)
        return

    if not output_override and os.path.exists(output_path):
        print(f"{output_path} already exists!", file=sys.stderr)
        return

    print(f"Building and compiling thumbnails for {input_file}...")

    video = cv2.VideoCapture(input_path)
    video_frame_count = int(video.get(cv2.CAP_PROP_FRAME_COUNT))
    output_image_count = int(output_rows * output_columns)
    video_fps = int(video.get(cv2.CAP_PROP_FPS))
    delay_in_seconds = int(video_fps * output_delay)
    offset_in_seconds = int(video_fps * output_offset)
    starting_frame = 0 + (delay_in_seconds + offset_in_seconds)  # delay
    current_frame = 0 + offset_in_seconds
    step_frame = int(video_frame_count // output_image_count)
    frames = []

    video.set(cv2.CAP_PROP_POS_FRAMES, starting_frame)  # fixed don't touch!
    for _ in tqdm(range(output_image_count), "Building thumbnails"):
        ret, frame = video.read()
        if current_frame <= video_frame_count:
            if output_resize != 100:
                frame_height, frame_width, _ = frame.shape
                new_frame_height = int(frame_height * (output_resize / 100))
                new_frame_width = int(frame_width * (output_resize / 100))
                frame = cv2.resize(frame, (new_frame_width, new_frame_height), interpolation=cv2.INTER_AREA)
            frames.append(frame)
            current_frame += step_frame
            video.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

    if len(frames) < output_image_count:
        print(f"{output_image_count - len(frames)} frames could not be built. Decrease the delay or offset.",
              file=sys.stderr)

    frame_height, frame_width, _ = frames[0].shape
    output_height = output_rows * frame_height
    output_width = output_columns * frame_width

    result_image = numpy.zeros((output_height, output_width, 3), numpy.uint8)

    for i, frame in enumerate(tqdm(frames, "Compiling thumbnails")):
        row = i // output_columns
        column = i % output_columns
        x = column * frame_width
        y = row * frame_height
        result_image[y:y + frame_height, x:x + frame_width] = frame

    try:
        cv2.imwrite(output_path, result_image)
        files_processed += 1
        print(f"Built and compiled thumbnails to {output_path}. [{files_processed}]")

    except OSError:
        print(f"Failed to save to {output_file}!", file=sys.stderr)

    video.release()
    cv2.destroyAllWindows()
