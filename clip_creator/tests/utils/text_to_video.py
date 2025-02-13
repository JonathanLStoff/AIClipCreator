
def find_text_sec(og_transcript:dict[str], sections:list[str], accuracy:float=70) -> None:
    '''
        Translate the sections that ai found into the timestamp of the original transcript.
        
        og_transcript: dict[str] - The original transcript of the video.
        sections: list[str] - The sections that the ai found.
        accuracy: float - % of the total number of words that need to be found.
        
    '''
    starting_timestamps: list[float] = []
    for section in sections:
        section = section.replace('\n', ' ')
        
        for value in og_transcript:
            fist_timestamp:float = 0
            words_found:int = 0
            total_words:int = len(section.split(' '))
            for section_word in section.split(' '):
                if section_word in value['text']:
                    words_found += 1
                    if fist_timestamp == 0:
                        fist_timestamp = value['start']
        if words_found / total_words * 100 >= accuracy:
            
    