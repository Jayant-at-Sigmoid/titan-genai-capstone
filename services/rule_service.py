import re
from typing import List, Dict, Any
from database.db import get_rules_list, add_rule, delete_rule
from utils.logger import app_logger

class ComplianceRuleService:
    @staticmethod
    def get_active_rules() -> List[Dict[str, Any]]:
        """Returns the list of current active rules in the system."""
        try:
            return get_rules_list()
        except Exception as e:
            app_logger.error(f"Failed to fetch rules from database: {e}")
            return []

    @staticmethod
    def create_new_rule(category: str, name: str, pattern: str, severity: str) -> bool:
        """Saves a new custom compliance rule to the system."""
        try:
            # Validate regex pattern compilation first
            re.compile(pattern)
            add_rule(category, name, pattern, severity)
            app_logger.info(f"Custom rule '{name}' added successfully under {category}.")
            return True
        except re.error as err:
            app_logger.error(f"Failed to compile regex pattern: {pattern}. Error: {err}")
            raise ValueError(f"Invalid regular expression: {err}")
        except Exception as e:
            app_logger.error(f"Failed to save rule: {e}")
            return False

    @staticmethod
    def remove_rule(rule_id: int) -> bool:
        """Deletes a compliance rule by ID."""
        try:
            delete_rule(rule_id)
            app_logger.info(f"Rule ID {rule_id} removed.")
            return True
        except Exception as e:
            app_logger.error(f"Failed to delete rule ID {rule_id}: {e}")
            return False

    def pre_check_text(self, text: str, category_filter: str = None) -> List[Dict[str, Any]]:
        """
        Scans a block of text using local regular expressions (pre-check step).
        Returns a list of identified candidate violations.
        """
        matches = []
        rules = self.get_active_rules()
        
        for rule in rules:
            if category_filter and rule["category"].lower() != category_filter.lower():
                continue
                
            try:
                pattern = re.compile(rule["pattern"])
                for match in pattern.finditer(text):
                    snippet_start = max(0, match.start() - 40)
                    snippet_end = min(len(text), match.end() + 40)
                    snippet = text[snippet_start:snippet_end].replace("\n", " ")
                    
                    matches.append({
                        "category": rule["category"],
                        "name": rule["name"],
                        "snippet": match.group(0),
                        "context_snippet": f"...{snippet}...",
                        "severity": rule["severity"],
                        "position": (match.start(), match.end())
                    })
            except Exception as e:
                app_logger.error(f"Failed parsing rule pattern '{rule['name']}': {e}")
                
        return matches

# Global reference instantiator
rule_service = ComplianceRuleService()
