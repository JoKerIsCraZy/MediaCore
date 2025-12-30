from typing import List, Dict, Any, Optional
from services.tmdb import tmdb_service
import logging
import asyncio

logger = logging.getLogger(__name__)


class FilterEngine:
    """
    Engine for applying filters to TMDB discover queries.
    
    Supported filter fields:
    - vote_average: Rating (0-10)
    - vote_count: Minimum votes
    - popularity: Popularity score
    - release_date: Release date range
    - year: Release year
    - genre: Genre IDs
    - with_keywords: TMDB keyword IDs
    - with_cast: Person IDs for cast
    - with_crew: Person IDs for crew
    - with_companies: Production company IDs
    - with_watch_providers: Streaming provider IDs
    - with_original_language: ISO 639-1 language code
    - certification: Age rating (e.g., "PG-13")
    - runtime: Runtime in minutes
    """
    
    # Mapping of our filter fields to TMDB API parameters
    FILTER_MAPPING = {
        # Rating filters
        "vote_average_gte": "vote_average.gte",
        "vote_average_lte": "vote_average.lte",
        "vote_average": "vote_average.gte",  # Alias for minimum rating
        "vote_count_gte": "vote_count.gte",
        "vote_count": "vote_count.gte",  # Alias

        # Date filters
        "release_date_gte": "primary_release_date.gte",
        "release_date_lte": "primary_release_date.lte",
        "year": "primary_release_year",

        # For TV shows
        "first_air_date_gte": "first_air_date.gte",
        "first_air_date_lte": "first_air_date.lte",
        "first_air_date_year": "first_air_date_year",

        # Genre filters
        "with_genres": "with_genres",
        "without_genres": "without_genres",

        # Other filters
        "with_keywords": "with_keywords",
        "without_keywords": "without_keywords",
        "with_cast": "with_cast",
        "with_crew": "with_crew",
        "with_people": "with_people",
        "with_companies": "with_companies",
        "with_watch_providers": "with_watch_providers",
        "watch_region": "watch_region",
        "with_original_language": "with_original_language",
        "with_origin_country": "with_origin_country",
        "with_runtime_gte": "with_runtime.gte",
        "with_runtime_lte": "with_runtime.lte",
        "with_runtime": "with_runtime.gte",  # Alias for minimum runtime

        # Release type (movies)
        "with_release_type": "with_release_type",

        # TV specific
        "with_status": "with_status",
        "with_type": "with_type",
        "with_networks": "with_networks",

        # Streaming monetization
        "with_watch_monetization_types": "with_watch_monetization_types",

        # Certification
        "certification": "certification",
        "certification_gte": "certification.gte",
        "certification_lte": "certification.lte",
        "certification_country": "certification_country",

        # Sorting
        "sort_by": "sort_by",

        # Include/exclude
        "include_adult": "include_adult",
        "include_video": "include_video",
    }
    
    # Valid sort options
    SORT_OPTIONS = {
        "movie": [
            "popularity.desc", "popularity.asc",
            "release_date.desc", "release_date.asc",
            "revenue.desc", "revenue.asc",
            "primary_release_date.desc", "primary_release_date.asc",
            "original_title.asc", "original_title.desc",
            "vote_average.desc", "vote_average.asc",
            "vote_count.desc", "vote_count.asc",
        ],
        "tv": [
            "popularity.desc", "popularity.asc",
            "first_air_date.desc", "first_air_date.asc",
            "vote_average.desc", "vote_average.asc",
            "vote_count.desc", "vote_count.asc",
        ],
    }
    
    def __init__(self):
        self.tmdb = tmdb_service
    
    def parse_filters(
        self,
        filters: List[Dict[str, Any]],
        operator: str = "and",
    ) -> Dict[str, Any]:
        """
        Parse filter list into TMDB API parameters.
        
        Filter format:
        {
            "field": "vote_average",
            "operator": "gte",
            "value": 7.0
        }
        """
        params = {}
        
        for f in filters:
            field = f.get("field", "")
            op = f.get("operator", "eq")
            value = f.get("value")
            
            if value is None:
                continue
            
            # Build parameter key
            param_key = self._build_param_key(field, op)
            if not param_key:
                continue
            
            # Map to TMDB parameter
            tmdb_param = self.FILTER_MAPPING.get(param_key, param_key)
            
            # Handle list values (genres, keywords, etc.)
            if isinstance(value, list):
                # For AND operator, use comma separation
                # For OR operator, use pipe separation
                separator = "," if operator == "and" else "|"
                value = separator.join(str(v) for v in value)
            
            params[tmdb_param] = value
        
        return params
    
    def _build_param_key(self, field: str, operator: str) -> Optional[str]:
        """Build parameter key from field and operator."""
        # Direct mapping for some fields
        direct_fields = [
            "with_genres", "without_genres", "with_keywords", "without_keywords",
            "with_cast", "with_crew", "with_people", "with_companies",
            "with_watch_providers", "watch_region", "with_watch_monetization_types",
            "with_original_language", "with_origin_country",
            "with_release_type", "with_status", "with_type", "with_networks",
            "certification", "certification_country",
            "sort_by", "year", "include_adult"
        ]
        if field in direct_fields:
            return field

        # Build compound key for range operators
        if operator in ["gte", "lte"]:
            return f"{field}_{operator}"

        return field
    
    async def discover(
        self,
        media_type: str = "movie",
        filters: List[Dict[str, Any]] = None,
        filter_operator: str = "and",
        sort_by: str = "popularity.desc",
        page: int = 1,
    ) -> Dict:
        """
        Discover media with filters applied.
        Supports multiple watch_regions and languages by querying each and merging results.

        Returns TMDB discover response with results.
        """
        filters = filters or []

        # Check if we have multiple watch_regions
        watch_region_filter = next((f for f in filters if f.get("field") == "watch_region"), None)
        watch_regions = []
        if watch_region_filter:
            value = watch_region_filter.get("value")
            if isinstance(value, list):
                watch_regions = value
            elif value:
                watch_regions = [value]

        # Check if we have multiple languages
        language_filter = next((f for f in filters if f.get("field") == "with_original_language"), None)
        languages = []
        if language_filter:
            value = language_filter.get("value")
            if isinstance(value, list):
                languages = value
            elif value:
                languages = [value]

        # If multiple regions or languages, query each combination and merge
        if len(watch_regions) > 1 or len(languages) > 1:
            return await self._discover_multi_param(
                media_type=media_type,
                filters=filters,
                filter_operator=filter_operator,
                sort_by=sort_by,
                page=page,
                watch_regions=watch_regions if len(watch_regions) > 1 else None,
                languages=languages if len(languages) > 1 else None,
            )

        # Single region or no region - normal query
        params = self.parse_filters(filters, filter_operator)

        # Add sorting
        if sort_by and sort_by in self.SORT_OPTIONS.get(media_type, []):
            params["sort_by"] = sort_by

        # Default: exclude adult content
        if "include_adult" not in params:
            params["include_adult"] = False

        # Make discover request
        result = await self.tmdb.discover(
            media_type=media_type,
            page=page,
            **params
        )

        # Normalize results
        normalized_results = [
            self.tmdb.normalize_result(item, media_type)
            for item in result.get("results", [])
        ]

        return {
            "results": normalized_results,
            "page": result.get("page", 1),
            "total_pages": result.get("total_pages", 0),
            "total_results": result.get("total_results", 0),
        }

    async def _discover_multi_param(
        self,
        media_type: str,
        filters: List[Dict[str, Any]],
        filter_operator: str,
        sort_by: str,
        page: int,
        watch_regions: List[str] = None,
        languages: List[str] = None,
    ) -> Dict:
        """Query multiple watch_regions and/or languages and merge results."""
        # Remove multi-value filters (we'll add them per-query)
        base_filters = [f for f in filters if f.get("field") not in ["watch_region", "with_original_language"]]

        # Add back single-value filters
        if watch_regions and len(watch_regions) == 1:
            base_filters.append({"field": "watch_region", "operator": "eq", "value": watch_regions[0]})
            watch_regions = None
        if languages and len(languages) == 1:
            base_filters.append({"field": "with_original_language", "operator": "eq", "value": languages[0]})
            languages = None

        # Build query combinations
        combinations = []
        if watch_regions and languages:
            # Both multi-value: query all combinations
            for region in watch_regions:
                for lang in languages:
                    combinations.append({"watch_region": region, "with_original_language": lang})
        elif watch_regions:
            combinations = [{"watch_region": region} for region in watch_regions]
        elif languages:
            combinations = [{"with_original_language": lang} for lang in languages]

        async def query_combination(combo: Dict) -> List[Dict]:
            combo_filters = base_filters.copy()
            for field, value in combo.items():
                combo_filters.append({"field": field, "operator": "eq", "value": value})

            params = self.parse_filters(combo_filters, filter_operator)
            if sort_by and sort_by in self.SORT_OPTIONS.get(media_type, []):
                params["sort_by"] = sort_by
            if "include_adult" not in params:
                params["include_adult"] = False

            result = await self.tmdb.discover(
                media_type=media_type,
                page=page,
                **params
            )
            return [
                self.tmdb.normalize_result(item, media_type)
                for item in result.get("results", [])
            ]

        # Query all combinations in parallel
        all_results = await asyncio.gather(*[
            query_combination(combo) for combo in combinations
        ])

        # Merge and deduplicate by tmdb_id
        seen_ids = set()
        merged_results = []
        for results in all_results:
            for item in results:
                if item["tmdb_id"] not in seen_ids:
                    seen_ids.add(item["tmdb_id"])
                    merged_results.append(item)

        # Sort merged results
        self._sort_results(merged_results, sort_by)

        return {
            "results": merged_results[:20],
            "page": page,
            "total_pages": 1,
            "total_results": len(merged_results),
        }

    def _sort_results(self, results: List[Dict], sort_by: str) -> None:
        """Sort results in place based on sort_by parameter."""
        if "popularity" in sort_by:
            reverse = sort_by.endswith(".desc")
            results.sort(key=lambda x: x.get("popularity", 0), reverse=reverse)
        elif "vote_average" in sort_by:
            reverse = sort_by.endswith(".desc")
            results.sort(key=lambda x: x.get("vote_average", 0), reverse=reverse)
        elif "release_date" in sort_by or "primary_release_date" in sort_by:
            reverse = sort_by.endswith(".desc")
            results.sort(key=lambda x: x.get("release_date", "") or "", reverse=reverse)
        elif "vote_count" in sort_by:
            reverse = sort_by.endswith(".desc")
            results.sort(key=lambda x: x.get("vote_count", 0), reverse=reverse)
    
    async def _fetch_external_id(self, item: Dict, media_type: str) -> Dict:
        """Fetch external IDs (IMDB/TVDB) for a single item."""
        try:
            external_ids = await self.tmdb.get_external_ids(item["tmdb_id"], media_type)
            if media_type == "movie":
                item["imdb_id"] = external_ids.get("imdb_id")
            else:  # tv
                item["imdb_id"] = external_ids.get("imdb_id")
                item["tvdb_id"] = external_ids.get("tvdb_id")
        except Exception as e:
            logger.warning(f"Failed to get external IDs for {item.get('title')}: {e}")
        return item

    async def get_all_results(
        self,
        media_type: str = "movie",
        filters: List[Dict[str, Any]] = None,
        filter_operator: str = "and",
        sort_by: str = "popularity.desc",
        limit: int = 100,
        fetch_external_ids: bool = True,
    ) -> List[Dict]:
        """
        Get all results up to limit, paginating as needed.
        Fetches external IDs (IMDB/TVDB) in parallel for faster export.
        Supports multiple watch_regions and languages by querying each separately.
        """
        filters = filters or []

        # Check for multiple watch_regions
        watch_region_filter = next((f for f in filters if f.get("field") == "watch_region"), None)
        watch_regions = []
        if watch_region_filter:
            value = watch_region_filter.get("value")
            if isinstance(value, list):
                watch_regions = value
            elif value:
                watch_regions = [value]

        # Check for multiple languages
        language_filter = next((f for f in filters if f.get("field") == "with_original_language"), None)
        languages = []
        if language_filter:
            value = language_filter.get("value")
            if isinstance(value, list):
                languages = value
            elif value:
                languages = [value]

        # Multi-param: query each combination, then merge
        if len(watch_regions) > 1 or len(languages) > 1:
            all_results = await self._get_all_results_multi_param(
                media_type=media_type,
                filters=filters,
                filter_operator=filter_operator,
                sort_by=sort_by,
                limit=limit,
                watch_regions=watch_regions if len(watch_regions) > 1 else None,
                languages=languages if len(languages) > 1 else None,
            )
        else:
            # Single region or no region - normal pagination
            all_results = []
            page = 1

            while len(all_results) < limit:
                result = await self.discover(
                    media_type=media_type,
                    filters=filters,
                    filter_operator=filter_operator,
                    sort_by=sort_by,
                    page=page,
                )

                results = result.get("results", [])
                if not results:
                    break

                all_results.extend(results)

                # Check if we've reached the last page
                if page >= result.get("total_pages", 1):
                    break

                page += 1

            # Trim to limit
            all_results = all_results[:limit]

        # Fetch external IDs in parallel (batched to avoid rate limiting)
        if fetch_external_ids and all_results:
            logger.info(f"Fetching external IDs for {len(all_results)} items...")
            batch_size = 40  # Process 40 items at a time (TMDB rate limit ~40/s)
            for i in range(0, len(all_results), batch_size):
                batch = all_results[i:i + batch_size]
                await asyncio.gather(*[
                    self._fetch_external_id(item, media_type)
                    for item in batch
                ])
            logger.info(f"Finished fetching external IDs")

        return all_results

    async def _get_all_results_multi_param(
        self,
        media_type: str,
        filters: List[Dict[str, Any]],
        filter_operator: str,
        sort_by: str,
        limit: int,
        watch_regions: List[str] = None,
        languages: List[str] = None,
    ) -> List[Dict]:
        """Get all results from multiple regions/languages, merged and deduplicated."""
        # Remove multi-value filters
        base_filters = [f for f in filters if f.get("field") not in ["watch_region", "with_original_language"]]

        # Add back single-value filters
        if watch_regions and len(watch_regions) == 1:
            base_filters.append({"field": "watch_region", "operator": "eq", "value": watch_regions[0]})
            watch_regions = None
        if languages and len(languages) == 1:
            base_filters.append({"field": "with_original_language", "operator": "eq", "value": languages[0]})
            languages = None

        # Build query combinations
        combinations = []
        if watch_regions and languages:
            for region in watch_regions:
                for lang in languages:
                    combinations.append({"watch_region": region, "with_original_language": lang})
        elif watch_regions:
            combinations = [{"watch_region": region} for region in watch_regions]
        elif languages:
            combinations = [{"with_original_language": lang} for lang in languages]

        num_combinations = len(combinations)
        pages_per_combo = max(1, limit // (20 * num_combinations) + 1)

        async def get_combo_results(combo: Dict) -> List[Dict]:
            """Get results for a single combination."""
            combo_filters = base_filters.copy()
            for field, value in combo.items():
                combo_filters.append({"field": field, "operator": "eq", "value": value})

            results = []
            page = 1

            while len(results) < limit and page <= pages_per_combo:
                params = self.parse_filters(combo_filters, filter_operator)
                if sort_by and sort_by in self.SORT_OPTIONS.get(media_type, []):
                    params["sort_by"] = sort_by
                if "include_adult" not in params:
                    params["include_adult"] = False

                result = await self.tmdb.discover(
                    media_type=media_type,
                    page=page,
                    **params
                )

                items = result.get("results", [])
                if not items:
                    break

                results.extend([
                    self.tmdb.normalize_result(item, media_type)
                    for item in items
                ])

                if page >= result.get("total_pages", 1):
                    break
                page += 1

            return results

        # Query all combinations in parallel
        logger.info(f"Querying {num_combinations} combinations...")
        all_results = await asyncio.gather(*[
            get_combo_results(combo) for combo in combinations
        ])

        # Merge and deduplicate
        seen_ids = set()
        merged_results = []
        for results in all_results:
            for item in results:
                if item["tmdb_id"] not in seen_ids:
                    seen_ids.add(item["tmdb_id"])
                    merged_results.append(item)

        # Sort merged results
        self._sort_results(merged_results, sort_by)

        logger.info(f"Found {len(merged_results)} unique items across {num_combinations} combinations")
        return merged_results[:limit]


# Singleton instance
filter_engine = FilterEngine()


# ============ Available Filters for Frontend ============

AVAILABLE_FILTERS = {
    "vote_average": {
        "label": "Rating",
        "type": "range",
        "min": 0,
        "max": 10,
        "step": 0.5,
        "operators": ["gte", "lte"],
    },
    "vote_count": {
        "label": "Minimum Votes",
        "type": "number",
        "min": 0,
        "operators": ["gte"],
    },
    "year": {
        "label": "Year",
        "type": "number",
        "operators": ["eq"],
    },
    "release_date": {
        "label": "Release Date",
        "type": "date",
        "operators": ["gte", "lte"],
    },
    "with_genres": {
        "label": "Genres (Include)",
        "type": "multi-select",
        "options_endpoint": "/api/genres/{media_type}",
        "operators": ["in"],
    },
    "without_genres": {
        "label": "Genres (Exclude)",
        "type": "multi-select",
        "options_endpoint": "/api/genres/{media_type}",
        "operators": ["in"],
    },
    "with_original_language": {
        "label": "Original Language",
        "type": "select",
        "options": [
            {"value": "en", "label": "English"},
            {"value": "de", "label": "German"},
            {"value": "fr", "label": "French"},
            {"value": "es", "label": "Spanish"},
            {"value": "it", "label": "Italian"},
            {"value": "ja", "label": "Japanese"},
            {"value": "ko", "label": "Korean"},
            {"value": "zh", "label": "Chinese"},
        ],
        "operators": ["eq"],
    },
    "with_watch_providers": {
        "label": "Streaming Service",
        "type": "multi-select",
        "options": [
            {"value": 8, "label": "Netflix"},
            {"value": 9, "label": "Amazon Prime Video"},
            {"value": 337, "label": "Disney+"},
            {"value": 2, "label": "Apple TV"},
            {"value": 350, "label": "Apple TV+"},
            {"value": 531, "label": "Paramount+"},
            {"value": 283, "label": "Crunchyroll"},
            {"value": 1899, "label": "Max"},
            {"value": 387, "label": "Peacock"},
            {"value": 15, "label": "Hulu"},
        ],
        "operators": ["in"],
    },
    "with_runtime": {
        "label": "Runtime (minutes)",
        "type": "range",
        "min": 0,
        "max": 300,
        "operators": ["gte", "lte"],
    },
    "certification": {
        "label": "Age Rating",
        "type": "select",
        "options": [
            {"value": "G", "label": "G"},
            {"value": "PG", "label": "PG"},
            {"value": "PG-13", "label": "PG-13"},
            {"value": "R", "label": "R"},
            {"value": "NC-17", "label": "NC-17"},
        ],
        "operators": ["eq", "lte"],
    },
}

SORT_OPTIONS_LIST = [
    {"value": "popularity.desc", "label": "Popularity (High to Low)"},
    {"value": "popularity.asc", "label": "Popularity (Low to High)"},
    {"value": "vote_average.desc", "label": "Rating (High to Low)"},
    {"value": "vote_average.asc", "label": "Rating (Low to High)"},
    {"value": "release_date.desc", "label": "Release Date (Newest)"},
    {"value": "release_date.asc", "label": "Release Date (Oldest)"},
    {"value": "vote_count.desc", "label": "Vote Count (High to Low)"},
    {"value": "revenue.desc", "label": "Revenue (High to Low)"},
]
