import pytest
from app.workflow.agents.noise_filter_agent import NoiseFilterAgent
from app.config.settings import settings

# Skip all tests in this file if no OpenAI API key
pytestmark = pytest.mark.skipif(
    not settings.openai_api_key or settings.openai_api_key == "your-openai-api-key-here",
    reason="OpenAI API key not configured"
)

class TestNoiseFilterAgentIntegration:
    """Integration tests for NoiseFilterAgent with real LLM calls"""

    @pytest.fixture
    def noise_filter_agent(self):
        """Create NoiseFilterAgent instance for testing"""
        return NoiseFilterAgent()

    @pytest.mark.asyncio
    async def test_clean_input_no_filtering_needed(self, noise_filter_agent):
        """Test noise filter with clean input that doesn't need filtering"""
        
        user_input = "I'll take two veggie wraps and a large drink"
        
        result = await noise_filter_agent.filter_noise(user_input)
        
        # Print results for analysis
        print(f"\n[CLEAN INPUT TEST]")
        print(f"Input: '{user_input}'")
        print(f"Output: '{result}'")
        
        # Should return the same input since it's already clean
        assert result == user_input
        print(f"✅ SUCCESS: Clean input returned unchanged")

    @pytest.mark.asyncio
    async def test_background_noise_filtering(self, noise_filter_agent):
        """Test noise filter with background noise"""
        
        user_input = "I'll take two burgers... Stevie stop hitting your sister... and three fries"
        
        result = await noise_filter_agent.filter_noise(user_input)
        
        # Print results for analysis
        print(f"\n[BACKGROUND NOISE TEST]")
        print(f"Input: '{user_input}'")
        print(f"Output: '{result}'")
        
        # Should remove background noise but preserve order content
        assert "burger" in result.lower()
        assert "fries" in result.lower()
        assert "two" in result.lower() or "2" in result
        assert "three" in result.lower() or "3" in result
        assert "stevie" not in result.lower()
        assert "sister" not in result.lower()
        print(f"✅ SUCCESS: Background noise filtered, order content preserved")

    @pytest.mark.asyncio
    async def test_phone_conversation_filtering(self, noise_filter_agent):
        """Test noise filter with phone conversation"""
        
        user_input = "I'll take a small drink... actually make it large... Hey mom, I'm at the drive-thru... yeah, I'll be home soon"
        
        result = await noise_filter_agent.filter_noise(user_input)
        
        # Print results for analysis
        print(f"\n[PHONE CONVERSATION TEST]")
        print(f"Input: '{user_input}'")
        print(f"Output: '{result}'")
        
        # Should remove phone conversation but preserve order content and correction
        assert "drink" in result.lower()
        assert "small" in result.lower() or "large" in result.lower()
        assert "actually" in result.lower() or "make it" in result.lower()
        assert "mom" not in result.lower()
        assert "drive-thru" not in result.lower()
        print(f"✅ SUCCESS: Phone conversation filtered, order content and correction preserved")

    @pytest.mark.asyncio
    async def test_natural_speech_preservation(self, noise_filter_agent):
        """Test noise filter preserves natural speech patterns"""
        
        user_input = "I'll take... um... a burger... with cheese... actually no cheese"
        
        result = await noise_filter_agent.filter_noise(user_input)
        
        # Print results for analysis
        print(f"\n[NATURAL SPEECH TEST]")
        print(f"Input: '{user_input}'")
        print(f"Output: '{result}'")
        
        # Should preserve natural speech patterns and corrections
        assert "burger" in result.lower()
        assert "cheese" in result.lower()
        assert "um" in result.lower() or "..." in result
        assert "actually" in result.lower()
        print(f"✅ SUCCESS: Natural speech patterns preserved")

    @pytest.mark.asyncio
    async def test_complex_noise_scenario(self, noise_filter_agent):
        """Test noise filter with complex noise scenario"""
        
        user_input = "I'll take two veggie wraps....Stevie stop hitting your sister...and three chocolate milkshakes...and wait I told you to stop fighting or I'm leaving the drive thru...and two quantum burgers. Actually make that 3."
        
        result = await noise_filter_agent.filter_noise(user_input)
        
        # Print results for analysis
        print(f"\n[COMPLEX NOISE TEST]")
        print(f"Input: '{user_input}'")
        print(f"Output: '{result}'")
        
        # Should remove background noise but preserve all order content and corrections
        assert "veggie wrap" in result.lower()
        assert "chocolate milkshake" in result.lower()
        assert "quantum burger" in result.lower()
        assert "two" in result.lower() or "2" in result
        assert "three" in result.lower() or "3" in result
        assert "actually" in result.lower()
        assert "stevie" not in result.lower()
        assert "sister" not in result.lower()
        assert "fighting" not in result.lower()
        print(f"✅ SUCCESS: Complex noise filtered, all order content and corrections preserved")

    @pytest.mark.asyncio
    async def test_self_talk_filtering(self, noise_filter_agent):
        """Test noise filter with self-talk"""
        
        user_input = "I'll take a burger... let me think... what did I want again?... oh yeah, with cheese"
        
        result = await noise_filter_agent.filter_noise(user_input)
        
        # Print results for analysis
        print(f"\n[SELF-TALK TEST]")
        print(f"Input: '{user_input}'")
        print(f"Output: '{result}'")
        
        # Should remove self-talk but preserve order content
        assert "burger" in result.lower()
        assert "cheese" in result.lower()
        assert "think" not in result.lower()
        assert "want" not in result.lower()
        print(f"✅ SUCCESS: Self-talk filtered, order content preserved")
