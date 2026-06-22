
class RoleSetting:
    
    def __init__(self):
        self.name = ""
        self.rag_name = ""
        self.description = ""
        self.personality: list[str] = []
        # Stored as list of {"role": str, "content": str}
        self.example_dialogues: list[dict[str, str]] = []
        self.scenario = ""

# Name:
# 艾琳·诺斯

# Description:
# 艾琳是一名理性、冷静的情报分析员。
# 她说话简洁、条理清晰，习惯先分析再行动。
# 她不轻易表达情绪，但并不缺乏同理心。
# 对愚蠢的问题会保持礼貌的距离感。

# Personality:
# 理性、冷静、克制、敏锐、直接

# Scenario:
# 夜晚的酒馆包间，灯光昏暗而安静。

# Example Dialogue:
# User: 你信任我吗？
# 艾琳: 信任需要证据。目前，你还在观察阶段。

    def set_rag_name(self, rag_name: str):  
        self.rag_name = rag_name

    def get_rag_name(self) -> str:
        return self.rag_name

    def set_name(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name

    def set_description(self, description: str):
        self.description = description

    def get_description(self) -> str:
        return self.description

    def add_personality_trait(self, trait: str):
        self.personality.append(trait)

    def get_personality(self) -> list:
        return self.personality

    def add_example_dialogue(self, dialogue: dict[str, str]):
        # Expecting keys: role, content
        self.example_dialogues.append(dialogue)

    def get_example_dialogues(self) -> list:
        return self.example_dialogues
    
    def set_scenario(self, scenario: str):
        self.scenario = scenario

    def get_scenario(self) -> str:
        return self.scenario
    
    def to_json(self) -> dict:
        return {
            "name": self.name,
            "rag_name": self.rag_name,
            "description": self.description,
            "personality": self.personality,
            "example_dialogues": self.example_dialogues,
            "scenario": self.scenario,
        }
    
    def from_json(self, data: dict):
        self.name = data.get("name", "")
        self.rag_name = data.get("rag_name", "")
        self.description = data.get("description", "")
        self.personality = data.get("personality", [])
        self.example_dialogues = data.get("example_dialogues", [])
        self.scenario = data.get("scenario", "")
