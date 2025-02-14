import math

from ollama import ChatResponse, chat
import base64


def find_sections(script:str, type_phases:str, wp_min:int=50, wp_max:int=200) -> list[str]:
    '''
        Find sections in a script based on a list of type phases using ai.
    '''
    responses: list[ChatResponse] = []
    script = script.replace('\n', ' ')
    if len(script.split(' ')) > 1000:
        
        script_runs = math.ceil(len(script.split(' ')) / 1000)
        for i in range(script_runs):
            if i == script_runs - 1:
                tmp_script = script.split(' ')[i*1000:]
            else:
                tmp_script = script.split(' ')[i*1000:(i+1)*1000]
            responses.append(chat(model='llama3.2', messages=[
                {
                    'role': 'system',
                    'content': f'''**"Analyze the following transcript and extract only the sections that contain {type_phases}. Each extracted section must:

                                Be between {wp_min}-{wp_max} words

                                Be genuinely {type_phases} in context

                                Keep original wording intact

                                Format requirements:

                                Separate each extracted segment with |

                                No ellipses (...) or partial sentences

                                No commentary or explanations

                                If no content meets these criteria, respond with 'No humorous segments found.'
                                Respond ONLY with the formatted extracts or the specified default message."**''',
                },
                {
                    'role': 'user',
                    'content': str(" ".join(tmp_script)),
                },
            ]
        ))
    else:
        responses.append(chat(model='llama3.2', messages=[
                {
                    'role': 'system',
                    'content': f'''**"Analyze the following transcript and extract only the sections that contain {type_phases}. Each extracted section must:

                                Be between {wp_min}-{wp_max} words

                                Be genuinely {type_phases} in context

                                Keep original wording intact

                                Format requirements:

                                Separate each extracted segment with |

                                No ellipses (...) or partial sentences

                                No commentary or explanations

                                If no content meets these criteria, respond with 'No humorous segments found.'
                                Respond ONLY with the formatted extracts or the specified default message."**''',
                },
                {
                    'role': 'user',
                    'content': script,
                },
            ]
            )
        )
    
    messages = []
    for response in responses:
        messages.extend(response.message.content.split('|'))
    return messages

def find_faces(image_path: str) -> list[list[float]]:
    """
    Analyze an image for face detection using ai.
    
    The function reads an image file, converts it to a Base64-encoded string,
    and sends it to an AI model for face detection. The AI is expected to return
    a slash-separated string of detected face bounding boxes in the format:
    "x,y,w,h,confidence". If no faces are found, it should respond with "No faces found."
    
    Returns a list of bounding boxes where each box is represented as
    [x, y, w, h, confidence]. If no faces are detected, returns an empty list.
    """
    
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
    
    response = chat(model='face-detection-model', messages=[
        {
            'role': 'system',
            'content': (
                'Analyze the following image (encoded in Base64) and detect faces. '
                'For each detected face, provide the bounding box as a comma-separated list: x,y,w,h,confidence. '
                'Separate multiple results with a slash ("/"). '
                'If no faces are found, respond with "No faces found."'
            ),
        },
        {
            'role': 'user',
            'content': encoded_image,
        },
    ])
    
    content = response.message.content.strip()
    if content == "No faces found.":
        return []
    
    boxes = []
    for entry in content.split('/'):
        parts = entry.split(',')
        if len(parts) == 5:
            try:
                box = [float(p) for p in parts]
                boxes.append(box)
            except ValueError:
                continue
    return boxes