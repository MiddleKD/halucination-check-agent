GET_SOURCE_AGENT_MODEL = "openai:gpt-3.5-turbo"
CONTEXT_CONSISTENCY_AGENT_MODEL = "openai:gpt-4o"
REASON_SUMMARY_AGENT_MODEL = "openai:gpt-4o"
DEFAULT_FALLBACK_LIMIT = 3
SCORE_DIFF_THRESHOLD = 0.3
GRAPH_PERSISTENCE_STATE_PATH_DIR = "./state"

DUMMY_CONTEXT = """
대한민국 홍길동씨는 롯데캐슬 18층에서 포메라니안 2마리와 골든리트리버 1마리를 키우고 있습니다.
홍길동씨는 삼성전자에 작년까지 다녔으나, 2025년 8월 4일부로 퇴사하였습니다.
홍길동씨는 현재 여자친구와 동거 중이며, 여자친구는 성춘향이고, 성춘향의 전 남친 이름은 이몽룡입니다.
"""

A2A_SEARCH_ENGINE_EXTENSION_URI = "enable_tavily_search_engine/v1"
A2A_SET_INPUT_CONTEXT_EXTENSION_URI = "set_input_context_explicitly/v1"