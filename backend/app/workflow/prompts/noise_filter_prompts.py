"""
Prompts for the noise filter agent
"""

def get_noise_filter_prompt(user_input: str) -> str:
    """
    Generate the prompt for noise filtering.
    
    Args:
        user_input: The raw user input that may contain background noise
        
    Returns:
        Formatted prompt string for the LLM
    """
    
    prompt = f"""You are a background noise filter for a drive-thru restaurant ordering system. Your job is to remove background noise while preserving ALL order-related content.

USER INPUT: "{user_input}"

TASK:
Remove background noise (phone calls, passenger chatter, unrelated conversations) while preserving:
- All food items mentioned
- All quantities and numbers
- All modifiers (with cheese, no pickles, extra lettuce, etc.)
- All sizes (small, medium, large, etc.)
- All corrections and changes (actually, wait, make that, etc.)
- Natural speech patterns (um, uh, like, you know)
- Hesitation and thinking out loud

WHAT TO REMOVE (Background Noise):
- Phone conversations: "Hey mom, I'm at the drive-thru... yeah, I'll be home soon"
- Passenger chatter: "Stevie stop hitting your sister", "Put your seatbelt on"
- Self-talk: "Let me think... what did I want again?"
- Unrelated topics: "How's the weather?", "Nice day, isn't it?"
- Technical issues: "Can you hear me?", "Is this thing working?"

WHAT TO PRESERVE (Order Content):
- All food items: "burger", "fries", "drink", "sandwich"
- All quantities: "two", "three", "a couple", "some"
- All modifiers: "with cheese", "no pickles", "extra lettuce"
- All sizes: "small", "large", "medium"
- Corrections: "actually make it large", "wait, make that three"
- Natural speech: "um", "uh", "like", "you know"
- Hesitation: "I'll take... um... a burger"

EXAMPLES:

Input: "I'll take a burger... um... with cheese... actually no cheese"
Output: "I'll take a burger... um... with cheese... actually no cheese"
(No background noise, preserve all order content)

Input: "I'll take two burgers... Stevie stop hitting your sister... and three fries"
Output: "I'll take two burgers and three fries"
(Remove passenger chatter, preserve order content)

Input: "I'll take a small drink... actually make it large... Hey mom, I'm at the drive-thru... yeah, I'll be home soon"
Output: "I'll take a small drink... actually make it large"
(Remove phone conversation, preserve order content and correction)

Input: "I'll take a burger... um... with cheese... and wait I told you to stop fighting or I'm leaving the drive thru... and two fries"
Output: "I'll take a burger... um... with cheese... and two fries"
(Remove passenger discipline, preserve order content and hesitation)

CRITICAL RULES:
1. When in doubt, PRESERVE the content rather than remove it
2. Only remove obvious background noise (phone calls, passenger chatter, unrelated topics)
3. Keep all order-related content including natural speech patterns
4. Preserve corrections and changes (actually, wait, make that)
5. If no background noise is present, return the input unchanged

Return ONLY the cleaned text, no explanations or additional text."""

    return prompt
