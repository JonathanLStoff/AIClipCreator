from googletrans import Translator
import asyncio

def translate_en_to(text, lang="es"):
    translator = Translator()
    translation = asyncio.run(translator.translate(text, src="en", dest=lang))
    return translation.text

if __name__ == "__main__":
    original_text = input("Enter text in English: ")
    spanish_text = translate_en_to(original_text)
    print("Translated to Spanish:", spanish_text)