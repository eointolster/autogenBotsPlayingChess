# autogenBotsPlayingChess
Three ollama bots. 1 referee mistral, player_black = llama2:7b, player_white = starling:7b 


This is for windows
Start up 5 or 6 powershells as admin

You need wsl installed, I have Ubuntu on top of that
Then:
  wsl -d Ubuntu

You need miniconda installed for my setup
  source activate autogen 
    pip install pyautogen, litellm

in the first powershell
Ollama serve
2nd powershell
litellm

3rd, 
litellm --model ollama/mistral:7b
4th
litellm --model ollama/llama2:7b
5th
litellm --model ollama/starling-lm:7b

Then CD into the area where you are running the code and 
python BotsVersion3.py
