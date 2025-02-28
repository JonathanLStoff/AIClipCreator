poetry run pip install git+https://github.com/huggingface/transformers.git@whisper_out_of_range
peotry run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
poetry run pip wheel --no-cache-dir --use-pep517 "playsound (==1.3.0)"