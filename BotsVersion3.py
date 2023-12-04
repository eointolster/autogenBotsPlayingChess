import chess, chess.svg, autogen, sys, os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Union

sys_msg = """You are an AI-powered chess board agent. 
Translate natural language into legal UCI moves. 
Reply only with a UCI move string."""

class RefereeAgent(autogen.AssistantAgent):
    board: chess.Board
    correct_move_messages: Dict[autogen.Agent, List[Dict]]

    # def __init__(self, board: chess.Board):
    #     super().__init__( name="RefereeAgent", system_message=sys_msg, llm_config={"temperature": 0.0}, max_consecutive_auto_reply=10, )
    #     self.register_reply(autogen.ConversableAgent, RefereeAgent._generate_board_reply)
    #     self.board = board
    #     self.correct_move_messages = defaultdict(list)

    def __init__(self, board: chess.Board, llm_config: dict):
        super().__init__(name="RefereeAgent", llm_config=llm_config)
        
        self.board = board
        self.correct_move_messages = defaultdict(list)

    def _generate_board_reply( self, messages: Optional[List[Dict]] = None, sender: Optional[autogen.Agent] = None, config: Optional[Any] = None, ) -> Union[str, Dict, None]:
        message = messages[-1]
        reply = self.generate_reply(self.correct_move_messages[sender] + [message], sender, exclude=[RefereeAgent._generate_board_reply])
        uci_move = reply if isinstance(reply, str) else str(reply["content"])
        try:
            self.board.push_uci(uci_move)
        except ValueError as e:
            return True, f"Error: {e}"
        else:
            print("Current board state:")
            print(self.board)
            self.correct_move_messages[sender].extend([message, self._message_to_dict(uci_move)])
            self.correct_move_messages[sender][-1]["role"] = "assistant"
            
            # Call the function to save the SVG
            self.save_board_state_as_svg()

            return True, uci_move
    
    def save_board_state_as_svg(self):
        moves_dir = 'moves'
        if not os.path.exists(moves_dir):
            os.makedirs(moves_dir)
        move_count = len(self.board.move_stack)
        svg_filename = os.path.join(moves_dir, f'move_{move_count}.svg')
        svg_output = chess.svg.board(self.board)
        with open(svg_filename, 'w') as file:
            file.write(svg_output)

sys_msg_tmpl = """Your name is {name} and you are a chess player.
You are playing against {opponent_name}.
You are playing as {color}.
You communicate your move using universal chess interface language.
You also chit-chat with your opponent when you communicate to light up the mood.
You should ensure both you and the opponent are making legal moves.
Do not apologise for making illegal moves."""

class ChessPlayerAgent(autogen.AssistantAgent):
    def __init__( self, color: str, referee_agent: RefereeAgent, max_turns: int, **kwargs, ):
        if color not in ["white", "black"]:
            raise ValueError(f"color must be either white or black, but got {color}")
        opponent_color = "black" if color == "white" else "white"
        name = f"Player {color}"
        opponent_name = f"Player {opponent_color}"
        sys_msg = sys_msg_tmpl.format( name=name, opponent_name=opponent_name, color=color, )
        super().__init__(name=name,system_message=sys_msg,max_consecutive_auto_reply=max_turns,**kwargs,)
        self.register_reply(ChessPlayerAgent, ChessPlayerAgent._generate_reply_for_player, config=referee_agent)        
        self.register_reply(RefereeAgent, ChessPlayerAgent._generate_reply_for_board, config=referee_agent.board)
        self.update_max_consecutive_auto_reply(referee_agent.max_consecutive_auto_reply(), referee_agent)

    def _generate_reply_for_player( self, messages: Optional[List[Dict]] = None, sender: Optional[autogen.Agent] = None, config: Optional[RefereeAgent] = None, ) -> Union[str, Dict, None]:
        referee_agent = config
        board_state_msg = [{"role": "system", "content": f"Current board:\n{referee_agent.board}"}]
        # propose a reply which will be sent to the board agent for verification.
        
        message = self.generate_reply(messages + board_state_msg, sender, exclude=[ChessPlayerAgent._generate_reply_for_player])
        if message is None:
            return True, None
        # converse with the board until a legal move is made or max allowed retries.
        self.initiate_chat(referee_agent, clear_history=False, message=message, silent=self.human_input_mode == "NEVER")
        last_message = self._oai_messages[referee_agent][-1]
        if last_message["role"] == "assistant":
            sys.stdout.write(f"{self.name}: I yield.\n")
            return True, None
        return True, self._oai_messages[referee_agent][-2]

    def _generate_reply_for_board( self, messages: Optional[List[Dict]] = None, sender: Optional[autogen.Agent] = None, config: Optional[chess.Board] = None, ) -> Union[str, Dict, None]:
        board = config
        board_state_msg = [{"role": "system", "content": f"Current board:\n{board}"}]
        last_message = messages[-1]
        if last_message["content"].startswith("Error"):
            last_message["role"] = "system"
            return True, self.generate_reply(messages + board_state_msg, sender, exclude=[ChessPlayerAgent._generate_reply_for_board])
        else:
            return True, None
max_turn = 20
board = chess.Board()



"""## Construct Agents"""

config_list_mistral = [
    {
        'base_url': "http://0.0.0.0:9286", # change your port to your from litellm
        'api_key': "NULL",
        'model': "ollama/mistral"
    }
]

config_list_llama2 = [
    {
        'base_url': "http://0.0.0.0:29006", # change your port to your from litellm
        'api_key': "NULL",
        'model': 'ollama/llama2:7b'
    }
]

config_list_starling = [
    {
        'base_url': "http://0.0.0.0:39395",# change your port to your from litellm
        'api_key': "NULL",
        'model': 'ollama/starling-lm:7b'
    }

]

llm_config_mistral={
        "config_list": config_list_mistral,
        "temperature": 0      

}

llm_config_llama2={
        "config_list": config_list_llama2,
        "temperature": 0.5,
        "cache_seed": 4

}

llm_config_starling={
        "config_list": config_list_starling,
        "temperature": 0.5,
        "cache_seed": 5
}

referee_agent = RefereeAgent(
    board=board,
    llm_config=llm_config_mistral
)

player_black = ChessPlayerAgent(
    color="black",
    referee_agent=referee_agent,
    max_turns=max_turn,
    llm_config=llm_config_llama2
)

player_white = ChessPlayerAgent(
    color="white",
    referee_agent=referee_agent,
    max_turns=max_turn,
    llm_config=llm_config_starling
)


# referee_agent = RefereeAgent(board=board, llm_config=umpire)

# player_black = ChessPlayerAgent(
#     color="black",
#     referee_agent=referee_agent,
#     max_turns=max_turn,
#     llm_config=llm_config_llama2,
# )


# player_white = ChessPlayerAgent(
#     color="white",
#     referee_agent=referee_agent,
#     max_turns=max_turn,
#     llm_config=llm_config_starling,
# )

# Start the game
player_black.initiate_chat(player_white, message="Your turn.")
