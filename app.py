import cv2
import ffmpeg
from multiprocessing import Pool, cpu_count
from src.remover import BackgroundRemover
import tempfile
import os


def process_frame(frame_data):
    frame, background_path, index = frame_data
    obj = BackgroundRemover()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    processed_frame = obj.process_video(frame, background_path)
    return processed_frame


def process_chunk(frames, background_path):
    with Pool(cpu_count()) as pool:
        processed_frames = pool.map(process_frame,
                                    [(frame, background_path, index) for index, frame in enumerate(frames)])
    return processed_frames


def write_chunk_to_video(frames, chunk_path, fps, width, height):
    out = cv2.VideoWriter(chunk_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))
    for frame in frames:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
    out.release()


def extract_audio(input_path, temp_dir):
    audio_path = os.path.join(temp_dir, 'audio.mp3')
    ffmpeg.input(input_path).output(audio_path).run(overwrite_output=True)
    return audio_path


def get_video_properties(video_capture):
    """Retrieve video properties like FPS, width, and height."""
    fps = int(video_capture.get(cv2.CAP_PROP_FPS))
    width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return fps, width, height


def process_video_chunks(video_capture, background_path, temp_dir, chunk_size, fps, width, height):
    """Process video in chunks, apply background, and save each chunk."""
    frame_index = 0
    current_chunk = []
    chunk_index = 0
    all_chunks = []

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        current_chunk.append(frame)
        frame_index += 1

        if len(current_chunk) == chunk_size:
            chunk_path = process_and_save_chunk(current_chunk, background_path, temp_dir, chunk_index, fps, width, height)
            all_chunks.append(chunk_path)
            current_chunk = []
            chunk_index += 1

    # Process remaining frames if any
    if current_chunk:
        chunk_path = process_and_save_chunk(current_chunk, background_path, temp_dir, chunk_index, fps, width, height)
        all_chunks.append(chunk_path)

    return all_chunks


def process_and_save_chunk(chunk, background_path, temp_dir, chunk_index, fps, width, height):
    """Apply background to a chunk of frames and save it as a video."""
    processed_chunk = process_chunk(chunk, background_path)
    chunk_path = os.path.join(temp_dir, f"chunk_{chunk_index}.mp4")
    write_chunk_to_video(processed_chunk, chunk_path, fps, width, height)
    return chunk_path


def create_concat_file(all_chunks, temp_dir):
    """Create a text file listing all chunk files for concatenation."""
    concat_file_path = os.path.join(temp_dir, 'concat_list.txt')
    with open(concat_file_path, 'w') as f:
        for chunk in all_chunks:
            f.write(f"file '{chunk}'\n")
    return concat_file_path


def concatenate_chunks(concat_file_path, temp_dir):
    """Concatenate all video chunks into a single video."""
    concatenated_video_path = os.path.join(temp_dir, 'concatenated_video.mp4')
    ffmpeg.input(concat_file_path, format='concat', safe=0).output(concatenated_video_path, c='copy').run()
    return concatenated_video_path


def merge_audio_and_video(video_path, audio_path, output_path):
    """Merge the concatenated video with the extracted audio."""
    ffmpeg.concat(
        ffmpeg.input(video_path),
        ffmpeg.input(audio_path),
        v=1, a=1).output(output_path).run()


def apply_background(input_path, output_path, background_path, chunk_size=100):
    video_capture = cv2.VideoCapture(input_path)
    fps, width, height = get_video_properties(video_capture)

    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = extract_audio(input_path, temp_dir)
        all_chunks = process_video_chunks(video_capture, background_path, temp_dir, chunk_size, fps, width, height)
        video_capture.release()

        concat_file_path = create_concat_file(all_chunks, temp_dir)
        concatenated_video_path = concatenate_chunks(concat_file_path, temp_dir)
        merge_audio_and_video(concatenated_video_path, audio_path, output_path)


if __name__ == "__main__":
    src = "/home/ubuntu/storage/input.mp4"
    dest = "/home/ubuntu/storage/output.mp4"
    bg = "/home/ubuntu/background-remove/static/background/green-screen.png"

    apply_background(src, dest, bg)
