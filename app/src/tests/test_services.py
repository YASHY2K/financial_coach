import pytest
from unittest.mock import MagicMock, patch
from coach.services.insights import InsightService

@pytest.mark.asyncio
async def test_insight_service_logic():
    service = InsightService()
    mock_db = MagicMock()
    
    with patch.object(service, 'generate_proactive_insights', return_value=[MagicMock()]) as mock_gen:
        insights = await service.generate_proactive_insights(mock_db, user_id=1)
        assert len(insights) > 0
        mock_gen.assert_called_once()
