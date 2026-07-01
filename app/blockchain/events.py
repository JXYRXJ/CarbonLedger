from typing import Dict, Any, List
from web3.contract import Contract
import logging
logger = logging.getLogger("app.blockchain.events")


def parse_contract_events(contract: Contract, event_name: str, receipt: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses and extracts logs for a specific event name from a transaction receipt.
    """
    try:
        event_func = getattr(contract.events, event_name)
        processed_logs = event_func().process_receipt(receipt)
        
        parsed_events = []
        for log in processed_logs:
            args = dict(log.get("args", {}))
            parsed_events.append({
                "event": log.get("event"),
                "address": log.get("address"),
                "block_number": log.get("blockNumber"),
                "transaction_hash": log.get("transactionHash").hex(),
                "args": args
            })
        return parsed_events
    except AttributeError:
        logger.error(f"Event name {event_name} does not exist on contract ABI")
        return []
    except Exception as e:
        logger.error(f"Error parsing events: {str(e)}")
        return []
