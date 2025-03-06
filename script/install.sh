poetry run pip install git+https://github.com/huggingface/transformers.git@whisper_out_of_range
poetry run pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install forcealign --no-dependencies
pip install g2p_en --no-dependencies

https://wkhtmltopdf.org/downloads.html

import nltk
nltk.download('averaged_perceptron_tagger_eng')

export PYTHONTRACEMALLOC=1

env LLVM_CONFIG=/Users/jonathanstoff/Documents/clangllvm-10.0.0/bin/llvm-config poetry add llvmlite==0.34.0
sudo port install llvm-10

cmake -G "Visual Studio 16 2019"
https://www.cgohlke.com/#llvmlite