# Suggested Question
PROFILE_QUESTION_TABLE_NAME = 'NlqSuggestedQuestion'
DEFAULT_PROMPT_NAME = 'suggested_question_prompt_default'
ACTIVE_PROMPT_NAME = 'suggested_question_prompt_active'

# Import BEDROCK_MODEL_IDS from env_var to support configuration via .env file
from utils.env_var import BEDROCK_MODEL_IDS