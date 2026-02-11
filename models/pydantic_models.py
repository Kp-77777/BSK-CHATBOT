from pydantic import BaseModel, Field

class StandaloneQuery(BaseModel):
    query: str = Field(
        description=(
            "ALWAYS return the query in English. Steps: "
            "1. Detect the input language "
            "2. If input is not English, translate it to English first "
            "3. Then reformulate as a standalone query with conversation context "
            "4. If no relevant history exists, return the current query (translated(if required) and grammar-corrected) "
            "The final output MUST be in English regardless of input language."
        )
    )
    language: str = Field(
        description="The detected language of the original input (e.g., 'English', 'Spanish', 'Hindi', 'Bengali')"
                    "See the overall sentence don't go by the scheme name,read and analyze carefully"
    )
