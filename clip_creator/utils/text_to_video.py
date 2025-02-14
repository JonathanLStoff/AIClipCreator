
def find_text_sec(og_transcript:dict[str], sections:list[str], accuracy:float=70):
    '''
        Translate the sections that ai found into the timestamp of the original transcript.
        
        og_transcript: dict[str] - The original transcript of the video.
        sections: list[str] - The sections that the ai found.
        accuracy: float - % of the total number of words that need to be found.
        
    '''
    starting_timestamps: list[list[float]] = []
    for section in sections:
        section = section.replace('\n', ' ')
        first_timestamp:float = 0
        words_found:int = 0
        running_duration:float = 0
        total_words:int = len(section.split(' '))
        not_found:int = 0
        for value in og_transcript:
            
            for section_word in section.split(' '):
                if section_word in value['text']:
                    words_found += 1
                    running_duration += value['duration']
                    if first_timestamp == 0:
                        fist_timestamp = value['start']
                elif first_timestamp != 0:
                    not_found += 1
                    if not_found > 5:
                        first_timestamp = 0
        if words_found / total_words * 100 >= accuracy:
            starting_timestamps.append([fist_timestamp, fist_timestamp + running_duration])
    return starting_timestamps
            
    