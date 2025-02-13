from ollama import chat
from ollama import ChatResponse


def find_sections(script:str, type_phases:str, wp_min:int=50, wp_max:int=200) -> list[str]:
    '''
    Find sections in a script based on a list of type phases using ai.
    '''
    response: ChatResponse = chat(model='llama3.2', messages=[
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
                'content': f'In the next message I Only pick it apart looking for {type_phases} in the text with max words {wp_max} and min words {wp_min}, needs to be divided by |. SCRIPT: {script}',
            },
        ]
    )

    
    return response.message.content.split('|')