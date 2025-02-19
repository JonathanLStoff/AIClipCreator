import math

import cv2
from ollama import ChatResponse, chat


def find_sections(
    script: str, type_phases: str, wp_min: int = 50, wp_max: int = 200
) -> list[str]:
    """
    Find sections in a script based on a list of type phases using ai.
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
                            "content": f"""**"Analyze the following transcript and extract only the sections that contain {type_phases}. Each extracted section must:

                                Be between {wp_min}-{wp_max} words

                                Be genuinely {type_phases} in context

                                Keep original wording intact

                                Format requirements:

                                Separate each extracted segment with |

                                No ellipses (...) or partial sentences

                                No commentary or explanations

                                If no content meets these criteria, respond with 'No humorous segments found.'
                                Respond ONLY with the formatted extracts or the specified default message."**""",
                        },
                        {
                            "role": "user",
                            "content": str(" ".join(tmp_script)),
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
                        "content": f"""**"Analyze the following transcript and extract only the sections that contain {type_phases}. Each extracted section must:

                                Be between {wp_min}-{wp_max} words

                                Be genuinely {type_phases} in context

                                Keep original wording intact

                                Format requirements:

                                Separate each extracted segment with |

                                No ellipses (...) or partial sentences

                                No commentary or explanations

                                If no content meets these criteria, respond with 'No humorous segments found.'
                                Respond ONLY with the formatted extracts or the specified default message."**""",
                    },
                    {
                        "role": "user",
                        "content": script,
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
