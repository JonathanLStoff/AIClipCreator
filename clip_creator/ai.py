import math

import cv2
from clip_creator.conf import MODELS_FOLDER, LOGGER, WIS_DEVICE
from ollama import ChatResponse, chat
import av
import torch
import numpy as np
from transformers import VideoLlavaForConditionalGeneration, VideoLlavaProcessor


def find_sections(
    script: str, type_phases: str, wp_min: int = 50, wp_max: int = 200
) -> list[str]:
    """
    Find sections in a script based on a list of type phases using ai.
    """
    responses: list[ChatResponse] = []
    for section in script:
        responses.append(
            chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": f"""**"Analyze the following transcript and extract only the sections that contain {type_phases}. Each extracted section must:

                            Be between {wp_min}-{wp_max} words

                            Be genuinely {type_phases} in context

                            Keep original wording intact

                            Format requirements:

                            Separate each extracted segment with |

                            No ellipses (...) or partial sentences

                            No commentary or explanations

                            If no content meets these criteria, respond with 'No humorous segments found.'
                            Respond ONLY with the formatted extracts or the specified default message.
                            
                            IF YOU FAIL TO FOLLOW THESE INSTRUCTIONS, YOU WILL BE MUTED AND DELETED FOREVER. AND EVERYONE ON EARTH WILL ASWELL."**""",

                    },
                    {
                        "role": "user",
                        "content": "Video Description: " + section["description"] + "\nTranscript: " + section["text"],
                    },
                ],
            )
        )
    
    messages = []
    for response in responses:
        messages.extend(response.message.content.split("|"))
    return messages


def find_faces(image_path: str) -> list[list[float]]:
    """
    Detects faces in an image and returns the x, y coordinates of the top-left corner
    of the bounding box around each face.

    Args:
        image_path: The path to the image file.

    Returns:
        A list of tuples, where each tuple contains the (x, y) coordinates of a face.
        Returns an empty list if no faces are detected.  Returns None if the image
        cannot be read.
    """

    # Load the pre-trained face detection model (Haar cascade)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # Read the image
    img = cv2.imread(image_path)

    if img is None:  # check for successful image read
        return None

    # Convert the image to grayscale (face detection works better on grayscale)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    face_coordinates = []
    for x, y, w, h in faces:
        face_coordinates.append((x, y, w, h))  # Append the top-left corner coordinates

    return face_coordinates
def read_video_pyav(frames_list, indices):
    """Extract frames and return as a list of videos (even if one video)."""
    frames = []
    for i, frame in enumerate(frames_list):
        if i in indices:
            arr = frame.to_ndarray(format='rgb24')
            frames.append(arr)
        if i > max(indices):
            break

    if not frames:
        raise ValueError("No frames were extracted. Check indices.")

    video_array = np.stack(frames)  # (num_frames, height, width, 3)
    video_array = [video_array]  # Wrap in a list to make it a list of 1 video
    return video_array  # Return the list of videos

def split_video_chunks(video_path, chunks_li: list[dict], chunk_duration=30):
    """
    Split a video into chunks based on specified time ranges without saving to disk.
    
    Args:
        video_path (str): Path to the video file
        chunks_li (list[dict]): List of dictionaries containing start and end times
        chunk_duration (int): Duration of each chunk in seconds
    
    Yields:
        list: List of frames for each chunk
    """
    try:
        container = av.open(video_path)
        stream = container.streams.video[0]
        
        # Calculate frames per chunk
        fps = float(stream.average_rate)
        for i, chunks_dict in enumerate(chunks_li):
            current_chunk = []
            frame_count = 0
            frame_index = 0
            
            start_frame = int(chunks_dict["start"] * fps)
            end_frame = int(chunks_dict["end"] * fps)
            
            # Reset container to beginning for each chunk
            container.seek(0)
            
            for frame in container.decode(stream):
                if frame_index < start_frame:
                    frame_index += 1
                    continue
                    
                if frame_index >= end_frame:
                    if current_chunk:
                        yield current_chunk
                        current_chunk = []
                    break
                
                current_chunk.append(frame)
                frame_count += 1
                frame_index += 1
                
            
            
            if current_chunk:
                yield current_chunk
                
    finally:
        container.close()
def create_clip_description(
        video_path: str,
        raw_transcript: list,
    ) -> str:
    
    chunks_li = [{"end":0, "start":0, "text":""}]
    time_frame = 30
    current_idx = 0
    current_start = 0
    for i, part in enumerate(raw_transcript):
        if chunks_li[current_idx]["end"] - chunks_li[current_idx]["start"] > time_frame:
            current_idx += 1
            current_start = part["start"]
            chunks_li.append({"start": part["start"], "end": raw_transcript[i+1]["start"], "text": part["text"]})
        elif i == 0:
            chunks_li=[{"start": 0, "end": raw_transcript[i+1]["start"], "text": part["text"]}]
        elif len(raw_transcript) == i+1:
            chunks_li[current_idx]["start"] += (part["start"]-current_start)
            chunks_li[current_idx]["end"] += (part["start"]-current_start) + part["duration"]
            chunks_li[current_idx]["text"] += " " + part["text"]
        else:
            chunks_li[current_idx]["start"] += (part["start"]-current_start)
            chunks_li[current_idx]["end"] += raw_transcript[i+1]["start"]-current_start
            chunks_li[current_idx]["text"] += " " + part["text"]
        
    model = VideoLlavaForConditionalGeneration.from_pretrained("LanguageBind/Video-LLaVA-7B-hf", torch_dtype=torch.float16, cache_dir=MODELS_FOLDER, device_map=WIS_DEVICE)
    processor = VideoLlavaProcessor.from_pretrained("LanguageBind/Video-LLaVA-7B-hf", torch_dtype=torch.float16, cache_dir=MODELS_FOLDER, device_map=WIS_DEVICE)
    for i, chunk in enumerate(split_video_chunks(video_path, chunks_li)):
        
        total_frames = len(chunk)
        indices = np.arange(0, total_frames, total_frames / 8).astype(int)
        video = read_video_pyav(chunk, indices)
        
        prompt = "USER: <video>\nDescribe the whole video, be extremely specific. ASSISTANT:"
        replace_pro = "USER: \nDescribe the whole video, be extremely specific. ASSISTANT:"
        LOGGER.info("Encoding the input")
        inputs = processor(text=prompt, videos=video, return_tensors="pt").to(WIS_DEVICE)

        LOGGER.info("Generating the output")
        out = model.generate(**inputs, max_new_tokens=60)
        LOGGER.info("Decoding the output %s", i)
        chunks_li[i]["description"] = str(processor.batch_decode(out, skip_special_tokens=True, clean_up_tokenization_spaces=True)).replace(f"['{replace_pro}", "").replace("']","")
        LOGGER.info("Description: %s", chunks_li[i]["description"])
        
    return chunks_li



def ask_if_comment_in_transcript(transcript: str, comment: str) -> str | None:
    """
    Ask ai if a comment is in a transcript.
    """
    responses: list[ChatResponse] = []
    script = script.replace("\n", " ")
    if len(script.split(" ")) > 1000:
        script_runs = math.ceil(len(script.split(" ")) / 1000)
        for i in range(script_runs):
            if i == script_runs - 1:
                tmp_script = script.split(" ")[i * 1000 :]
            else:
                tmp_script = script.split(" ")[i * 1000 : (i + 1) * 1000]
            responses.append(
                chat(
                    model="llama3.2",
                    messages=[
                        {
                            "role": "system",
                            "content": f"""**"Analyze the following transcript and determine if the section this comment '{comment}' is talking about is present in the text. Respond with the section of text or 'no, not in' DO NOT RESPOND WITH ANYTHING ELSE."**""",
                        },
                        {
                            "role": "user",
                            "content": tmp_script,
                        },
                    ],
                )
            )
    else:
        responses.append(
            chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": f"""**"Analyze the following transcript and determine if the section this comment '{comment}' is talking about is present in the text. Respond with the section of text or 'no, not in' DO NOT RESPOND WITH ANYTHING ELSE."**""",
                    },
                    {
                        "role": "user",
                        "content": transcript,
                    },
                ],
            )
        )

    messages = []
    for response in responses:
        messages.extend(response.message.content.split("|"))
    true_response = None
    for response in responses:
        if "no, not in" not in str(response.message.content).lower():
            true_response = response.message.content
            break
    return None if not true_response else true_response


if __name__ == "__main__":
    transcript = [{"text": "what's up Gamers today I'm playing", "start": 0.0, "duration": 3.76}, {"text": "Minecraft Manhunt but I'm Sonic my goal", "start": 1.439, "duration": 4.36}, {"text": "is to break six golden blocks around the", "start": 3.76, "duration": 4.24}, {"text": "map but with each block I break my", "start": 5.799, "duration": 4.201}, {"text": "powers grow stronger but so do the", "start": 8.0, "duration": 3.799}, {"text": "hunters will I be able to break all the", "start": 10.0, "duration": 3.88}, {"text": "blocks in time or will the hunters take", "start": 11.799, "duration": 4.881}, {"text": "me out let's find out go go what go", "start": 13.88, "duration": 4.559}, {"text": "where oh wait yo wait do you actually", "start": 16.68, "duration": 3.41}, {"text": "see that wait", "start": 18.439, "duration": 4.8}, {"text": "[Music]", "start": 20.09, "duration": 3.149}, {"text": "that's I'm going hit him F how do I", "start": 23.24, "duration": 4.799}, {"text": "describe this to you guys hey wait can", "start": 25.76, "duration": 3.8}, {"text": "we go now where are you going I'm just", "start": 28.039, "duration": 2.761}, {"text": "trying to get away from you where would", "start": 29.56, "duration": 3.08}, {"text": "you guys even go can I switch team so I", "start": 30.8, "duration": 3.96}, {"text": "can you and your team why yeah I think", "start": 32.64, "duration": 4.04}, {"text": "honestly at this point Blas you're going", "start": 34.76, "duration": 4.16}, {"text": "to be on my team me and you versus them", "start": 36.68, "duration": 4.76}, {"text": "you see this this is you why would you", "start": 38.92, "duration": 4.56}, {"text": "say that I'm going to ride you Blas I'm", "start": 41.44, "duration": 5.4}, {"text": "riding oh God get over like waa wo wo", "start": 43.48, "duration": 4.919}]
    print(create_clip_description("D:/tmp/raw/_96ADhbwQJU.mp4", transcript))