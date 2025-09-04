from langchain_openai import ChatOpenAI

from agent.model.model_settings import MODEL_SETTINGS

model = ChatOpenAI(**MODEL_SETTINGS["primary"])
