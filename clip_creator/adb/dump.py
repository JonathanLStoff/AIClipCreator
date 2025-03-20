import uiautomator2 as u2
from clip_creator.conf import LOGGER, ADB_DEVICE, ADB_PATH, ADB_PATH_EXE, ADB_SHELL, POSSIBLE_TRANSLATE_LANGS_TTS
import json
def dump():
    d = u2.connect(ADB_DEVICE)
    xml=d.dump_hierarchy()
    with open("dump.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    LOGGER.info("Dumped XML to dump.xml")
    d.stop_uiautomator()
    
if __name__ == "__main__":

    d = u2.connect(ADB_DEVICE)
    xml=d.dump_hierarchy()
    with open("dump.xml", "w", encoding="utf-8") as f:
        f.write(xml)
    print("Dumped XML to dump.xml")
    d.stop_uiautomator()