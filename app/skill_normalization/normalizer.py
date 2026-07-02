"""
SkillNormalizer — Implementation of the skill name normalization algorithm in ARIS.
Normalizes arbitrary raw resume skill inputs against the structured alias repository.
"""

import os
import json
import logging
import re
from typing import List, Dict, Any, Tuple

from app.skill_normalization.models import NormalizedSkill
from app.skill_normalization.exceptions import (
    SkillNormalizationError,
    AliasFileNotFoundError,
    InvalidAliasFormatError,
)

logger = logging.getLogger("aris.skill_normalization")


class SkillNormalizer:
    """
    Service class that loads a skill alias repository and normalizes raw skill strings
    into their canonical equivalent names with associated confidence scores.
    """

    def __init__(self, alias_file_path: str = "data/skill_graph/skill_aliases.json") -> None:
        """
        Initializes the SkillNormalizer and pre-compiles lookup index mappings.

        Args:
            alias_file_path: The file path to the skill aliases configuration JSON.
            
        Raises:
            AliasFileNotFoundError: If the config file cannot be found.
            InvalidAliasFormatError: If the JSON cannot be parsed.
        """
        self.alias_file_path = alias_file_path
        self.aliases: Dict[str, List[str]] = {}
        self.clean_aliases: Dict[str, str] = {}
        self._load_aliases()

    def _load_aliases(self) -> None:
        """
        Loads the raw aliases file and builds indexes for direct and punctuation-cleaned lookup.
        """
        if not os.path.exists(self.alias_file_path):
            logger.error("Alias file not found at: %s", self.alias_file_path)
            raise AliasFileNotFoundError(f"Alias configuration file not found at: {self.alias_file_path}")

        try:
            with open(self.alias_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse alias JSON: %s", str(e))
            raise InvalidAliasFormatError(f"Failed to parse invalid alias JSON: {str(e)}") from e
        except Exception as e:
            logger.error("Unexpected error reading alias file: %s", str(e))
            raise SkillNormalizationError(f"Unexpected error loading aliases: {str(e)}") from e

        if not isinstance(data, dict):
            raise InvalidAliasFormatError("Aliases configuration file must be a JSON object dictionary.")

        # Process and build internal lookup tables
        self.aliases = {}
        self.clean_aliases = {}

        for alias, content in data.items():
            if not isinstance(content, dict) or "canonical" not in content:
                logger.warning("Skipping invalid entry in alias file for key: '%s'", alias)
                continue

            canonical = content["canonical"]
            if isinstance(canonical, str):
                canonical_list = [canonical]
            elif isinstance(canonical, list):
                canonical_list = [str(item) for item in canonical]
            else:
                logger.warning("Skipping invalid canonical format for key: '%s'", alias)
                continue

            alias_lower = alias.lower().strip()
            self.aliases[alias_lower] = canonical_list

            # Index the punctuation-cleaned alias string
            cleaned_key = re.sub(r'[^a-z0-9]', '', alias_lower)
            if cleaned_key:
                if cleaned_key not in self.clean_aliases:
                    self.clean_aliases[cleaned_key] = alias_lower

        logger.info(
            "Successfully initialized SkillNormalizer with %d aliases (%d cleaned lookup paths).",
            len(self.aliases),
            len(self.clean_aliases)
        )

    def normalize(self, skill: str) -> List[NormalizedSkill]:
        """
        Normalizes a single skill string according to the normalization algorithm rules.

        Args:
            skill: Raw skill string to resolve.

        Returns:
            A list of NormalizedSkill Pydantic model objects.
        """
        if not skill or not isinstance(skill, str):
            logger.warning("Invalid raw skill input provided for normalization: %s", skill)
            return []

        # 1. Convert to lowercase and trim whitespace
        skill_clean = skill.lower().strip()

        matched_canonical: List[str] = []

        # 2. Check direct lookup in aliases
        if skill_clean in self.aliases:
            matched_canonical = self.aliases[skill_clean]
            logger.debug("Direct alias match found for '%s': %s", skill, matched_canonical)
        else:
            # 3. Try punctuation-normalized lookup (fallback)
            stripped_query = re.sub(r'[^a-z0-9]', '', skill_clean)
            if stripped_query in self.clean_aliases:
                orig_key = self.clean_aliases[stripped_query]
                matched_canonical = self.aliases[orig_key]
                logger.debug("Punctuation-normalized alias match found for '%s' -> '%s': %s", skill, orig_key, matched_canonical)

        # 4. Resolve candidate outputs based on lookup outcomes
        if not matched_canonical:
            # If no alias exists, return the original skill with confidence = 100%
            original_trimmed = skill.strip()
            logger.info("No matching alias found for '%s'. Returning original skill with 100%% confidence.", original_trimmed)
            return [NormalizedSkill(canonical=original_trimmed, confidence=100)]

        if len(matched_canonical) == 1:
            # One canonical skill exists, return confidence = 100%
            return [NormalizedSkill(canonical=matched_canonical[0], confidence=100)]
        else:
            # Multiple canonical skills exist, return confidence = 50% for each
            return [
                NormalizedSkill(canonical=item, confidence=50)
                for item in matched_canonical
            ]

    def normalize_list(self, skills: List[str]) -> Tuple[List[str], Dict[str, Any]]:
        """
        Normalizes a list of raw skills and builds a mapping from canonical terms back to raw inputs.

        Args:
            skills: A list of raw skill strings.

        Returns:
            A tuple of (normalized_skills_list, canonical_to_raw_map).
        """
        normalized_skills = []
        canonical_to_raw_map = {}

        for skill in skills:
            normalized = self.normalize(skill)
            for norm_skill in normalized:
                canonical = norm_skill.canonical
                normalized_skills.append(canonical)
                
                # Check confidence to format mapping
                if norm_skill.confidence == 100:
                    canonical_to_raw_map[canonical] = skill
                else:
                    canonical_to_raw_map[canonical] = (skill, norm_skill.confidence)

        # Deduplicate canonical list while preserving order
        seen = set()
        deduped_normalized = []
        for sk in normalized_skills:
            if sk not in seen:
                seen.add(sk)
                deduped_normalized.append(sk)

        return deduped_normalized, canonical_to_raw_map
