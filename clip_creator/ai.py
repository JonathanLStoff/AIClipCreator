import math

from ollama import ChatResponse, chat


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